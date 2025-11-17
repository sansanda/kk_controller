# This is a sample Python script.
import csv
import json
from typing import Dict, Any
from datetime import datetime

from devices.base import Source
from utils.delays.delays import DelayFactory, Delay
from devices import VisaResourceManager, Keithley2400, KeysightE4990A, Multimeter


# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



def get_delay(settings: Dict['str', Any], callback_function=None) -> Delay:
    delay_type = settings["selected_delay"]
    delay = None
    if delay_type == "TimeDelay":
        delay = DelayFactory.create_delay(
            delay_type,
            timeout=settings["time_delay"]["delay_value"],
            callback=callback_function
        )
    elif delay_type == "StatisticsDelay":
        delay = DelayFactory.create_delay(
            delay_type,
            reference_value=1.0,
            metric=settings["statistics_delay"]["metric"],
            comparator=settings["statistics_delay"]["comparator"],
            timer_interval=settings["statistics_delay"]["timer_interval"],
            callback=None,
            read_value=lambda: callback_function
        )
    else:
        raise ValueError(f"Tipo de delay no soportado: {delay_type}")
    return delay


def main_sdm_loop(sweep_config: dict,
                  source: Source,
                  meter: Multimeter,
                  imp_analyzer: KeysightE4990A,
                  delay,
                  output_file_name,
                  log: bool = True):
    # Generar puntos de barrido
    start = sweep_config["start_voltage"]
    stop = sweep_config["stop_voltage"]
    num_points = sweep_config["number_of_points"]
    voltages = [start + i * (stop - start) / (num_points - 1) for i in range(num_points)]

    # Bucle principal SDM
    source.output(True)
    for v in voltages:
        print(f"\nAplicando voltaje: {v:.3f} V")
        source.set_source_value(v)
        print("Iniciando delay...")
        delay.start()
        while not delay.is_done():
            pass
        z, phi, cs = imp_analyzer.measure()
        z_mean = sum(z) / len(z)
        phi_mean = sum(phi) / len(phi)
        cs_mean = sum(cs) / len(cs)

        # Guardar fila en el CSV
        with open(output_file_name, mode="a", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([f"{v:.3f}", f"{z_mean:.5e}", f"{phi_mean:.5e}", f"{cs_mean:.5e}"])

    source.output(False)

def main():
    # carga del JSON para la configuracion
    with open("setting/settings_measure.json", "r") as f:
        settings = json.load(f)

    visa_settings = settings["Visa"]
    source_meter_settings = settings["Instruments"]["SourceMeter"]
    impedance_analyzer_settings = settings["Instruments"]["ImpedanceAnalyzer"]
    sweep_settings = settings["Sweep"]
    delay_settings = settings["Delays"]
    output_file_settings = settings["Results"]

    #backend VISA
    visa = VisaResourceManager(backend=visa_settings["backend"],
                               timeout_ms=visa_settings["timeout_ms"])

    print("Recursos VISA:", visa.list_resources())

    # --- SourceMeter ---
    smu_res = visa.open(source_meter_settings["gpib_addr"])
    smu = Keithley2400(smu_res, source_meter_settings)

    # --- Impedance Analyzer ---
    imp_res = visa.open(impedance_analyzer_settings["gpib_addr"])
    imp_analyzer = KeysightE4990A(imp_res, impedance_analyzer_settings)

    delay = get_delay(delay_settings, callback_function=None)

    # init output file
    # Abrir fichero y escribir cabecera
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{output_file_settings['File']['name']}_{timestamp}.csv"

    with open(file_name, mode="w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([h.strip() for h in output_file_settings["File"]["header"].split(",")])

    # Ejecutar el bucle principal
    main_sdm_loop(sweep_settings, smu, smu, imp_analyzer, delay, file_name)


if __name__ == "__main__":
    main()
