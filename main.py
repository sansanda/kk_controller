# This is a sample Python script.
import time
import json
import timeit
import numpy as np
import struct
from utils.delays.delays import DelayFactory, TimeDelay, StatisticsDelay
from devices import (
    VisaResourceManager,
    Keithley2400,
    KeysightE4990A,
)
# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


from config import GPIB_ADDRESS_SOURCEMETER, GPIB_ADDRESS_IMPEDANCE_ANALYZER
from devices.base import AmmeterBase


def configure_smu(smu):
    print("SMU:", smu.idn())
    smu.reset()
    smu.configure_data_format_elements(['CURR'])
    smu.set_source_mode('V')
    smu.set_source_range(1000)
    smu.set_measure_function('I')
    smu.set_compliance(1E-3)
    smu.set_measure_range('AUTO')
    smu.enable_remote_sense(False)
    smu.set_nplc(0.01)
    smu.set_terminals("FRONT")


def configure_impedance_analyzer(imp_analyzer, f_start, f_stop, Vac, points):
    """Setup point-triggered sweep, Cs/Rs parameters, no DC bias."""
    imp_analyzer.write("TRIG:SOUR BUS")
    imp_analyzer.write("INIT1:CONT ON")
    imp_analyzer.write("CALC1:PAR:COUN 3")
    imp_analyzer.write("CALC1:PAR1:DEF Z")
    imp_analyzer.write("CALC1:PAR2:DEF TZ")
    imp_analyzer.write("CALC1:PAR3:DEF CS")
    imp_analyzer.write("DISP:WIND1:SPL D1_2_3")

    imp_analyzer.write("SENS1:SWE:TYPE LIN")
    imp_analyzer.write(f"SENS1:FREQ:STAR {f_start}")
    imp_analyzer.write(f"SENS1:FREQ:STOP {f_stop}")
    imp_analyzer.write(f"SENS1:SWE:POIN {points}")

    imp_analyzer.write(f"SOUR1:VOLT {Vac}")

    imp_analyzer.write("SOUR:BIAS:STAT OFF")

    print("\n--- Measurement Configuration ---")
    print(f"Points: {points}")
    print(f"Range: {f_start / 1e3:.2f} – {f_stop / 1e3:.2f} kHz")
    print(f"AC level: {Vac} V (no DC bias)")
    print("---------------------------------\n")


def imp_analyzer_measure(imp_analyzer, npoints):
    """Read Cs and Rs traces, handle interleaved data correctly."""
    imp_analyzer.write("INIT1:CONT OFF")
    imp_analyzer.write("ABOR")  # aborts current measurement
    imp_analyzer.write("INIT1:CONT ON")
    imp_analyzer.write("TRIG:SING")  # trigger single
    imp_analyzer.query("*OPC?")

    imp_analyzer.write("FORM:DATA ASCII")
    imp_analyzer.write("CALC1:PAR1:SEL")
    imp_analyzer.write("CALC1:DATA:FDAT?")
    z_data = imp_analyzer.read()

    # Convertir la cadena en una lista de floats
    float_values = [float(val) for val in z_data.split(',')]

    # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
    z_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

    imp_analyzer.write("CALC1:PAR2:SEL")
    imp_analyzer.write("CALC1:DATA:FDAT?")
    phi_data = imp_analyzer.read()

    # Convertir la cadena en una lista de floats
    float_values = [float(val) for val in phi_data.split(',')]

    # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
    phi_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

    imp_analyzer.write("CALC1:PAR3:SEL")
    imp_analyzer.write("CALC1:DATA:FDAT?")
    cs_data = imp_analyzer.read()

    # Convertir la cadena en una lista de floats
    float_values = [float(val) for val in cs_data.split(',')]

    # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
    cs_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

    return z_data, phi_data, cs_data


def main_sdm_loop(config: dict, keithley: Keithley2400, log: bool = True):

    def measure():
        print('Measuring....')

    sweep_cfg = config["Sweep"]
    instr_cfg = config["Instruments"]["SourceMeter"]

    if log:
        print("=== CONFIGURACIÓN IMPORTADA DEL JSON ===")
        print(f"Instrumento: {instr_cfg['model']}")
        print(f"Modo de fuente: {instr_cfg['source_mode']}")
        print(f"Rango de fuente: {instr_cfg['source_range']}")
        print(f"Función de medida: {instr_cfg['measure_function']}")
        print(f"NPLC: {instr_cfg['nplc']}")
        print(f"Terminales: {instr_cfg['front_rear']}")
        print(f"Remote sense: {instr_cfg['remote_sense']}")
        print(f"Compliance: {sweep_cfg['compliance']}")
        print(f"Tipo de delay: {sweep_cfg['selected_delay']}")
        print(f"Número de puntos: {sweep_cfg['number_of_points']}")
        print("========================================\n")

    # Configurar el instrumento
    keithley.set_source_mode(instr_cfg["source_mode"])
    keithley.set_compliance(sweep_cfg["compliance"])
    keithley.set_source_range(instr_cfg["source_range"])
    keithley.set_measure_function(instr_cfg["measure_function"])
    keithley.set_nplc(instr_cfg["nplc"])
    keithley.set_terminals(instr_cfg["front_rear"])
    keithley.enable_remote_sense(instr_cfg["remote_sense"].lower() == "y")

    # Crear el delay
    delay_type = sweep_cfg["selected_delay"]
    if delay_type == "time":
        delay = DelayFactory.create_delay(
            delay_type,
            timeout=sweep_cfg["time_delay"]["delay_value"],
            callback=measure
        )
    elif delay_type == "statistics":
        delay = DelayFactory.create_delay(
            delay_type,
            reference_value=1.0,
            metric=sweep_cfg["statistics_delay"]["metric"],
            comparator=sweep_cfg["statistics_delay"]["comparator"],
            timer_interval=sweep_cfg["statistics_delay"]["timer_interval"],
            callback=measure,
            read_value=lambda: keithley.measure_current
        )
    else:
        raise ValueError(f"Tipo de delay no soportado: {delay_type}")

    print(delay)

    # Generar puntos de barrido
    start = sweep_cfg["start_voltage"]
    stop = sweep_cfg["stop_voltage"]
    num_points = sweep_cfg["number_of_points"]
    voltages = [start + i * (stop - start) / (num_points - 1) for i in range(num_points)]

    # Bucle principal SDM
    for v in voltages:
        print(f"\nAplicando voltaje: {v:.3f} V")
        keithley.set_source_value(v)

        print("Iniciando delay...")
        delay.start()
        while not delay.is_done():
            pass

def main():
    # Configura tu backend VISA y direcciones GPIB:
    BACKEND = "@ni"  # "@ni", "@keysight", "@py", "@sim"

    visa = VisaResourceManager(backend=BACKEND, timeout_ms=30000)
    print("Recursos VISA:", visa.list_resources())

    # --- SourceMeter ---
    smu_res = visa.open(GPIB_ADDRESS_SOURCEMETER)
    smu = Keithley2400(smu_res)
    # configure_smu(smu)

    # --- Impedance Analyzer ---
    imp_res = visa.open(GPIB_ADDRESS_IMPEDANCE_ANALYZER)
    imp_analyzer = KeysightE4990A(imp_res)

    # Simulación de carga del JSON
    with open("./config/config_measure.json", "r") as f:
        config = json.load(f)

    # Ejecutar el bucle principal
    main_sdm_loop(config, smu)

    # # --- SourceMeter ---
    # smu_res = visa.open(GPIB_ADDRESS_SOURCEMETER)
    # smu = Keithley2400(smu_res)
    # configure_smu(smu)
    #
    # # --- Impedance Analyzer ---
    # imp_res = visa.open(GPIB_ADDRESS_IMPEDANCE_ANALYZER)
    # imp_analyzer = KeysightE4990A(imp_res)
    # configure_impedance_analyzer(imp_analyzer, 100e3, 100e3, 0.5, 3)
    # imp_analyzer_measured_data = imp_analyzer_measure(imp_analyzer)

    # bucle princial SDM

    # z, p, c = (imp_analyzer_measured_data[0][1], imp_analyzer_measured_data[1][1], imp_analyzer_measured_data[2][1])

if __name__ == "__main__":
    main()
