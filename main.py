# This is a sample Python script.
import csv
import time
import json
import timeit
from typing import Dict, Any

import numpy as np
import struct
from utils.delays.delays import DelayFactory, TimeDelay, StatisticsDelay, Delay
from devices import (
    VisaResourceManager,
    Keithley2400,
    KeysightE4990A,
)

from datetime import datetime

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


from config import GPIB_ADDRESS_SOURCEMETER, GPIB_ADDRESS_IMPEDANCE_ANALYZER
from devices.base import AmmeterBase, SourcemeterBase


def get_delay(delay_config: Dict['str', Any], callback_function=None) -> Delay:
    delay_type = delay_config["selected_delay"]
    delay = None
    if delay_type == "TimeDelay":
        delay = DelayFactory.create_delay(
            delay_type,
            timeout=delay_config["time_delay"]["delay_value"],
            callback=callback_function
        )
    elif delay_type == "StatisticsDelay":
        delay = DelayFactory.create_delay(
            delay_type,
            reference_value=1.0,
            metric=delay_config["statistics_delay"]["metric"],
            comparator=delay_config["statistics_delay"]["comparator"],
            timer_interval=delay_config["statistics_delay"]["timer_interval"],
            callback=None,
            read_value=lambda: callback_function
        )
    else:
        raise ValueError(f"Tipo de delay no soportado: {delay_type}")
    return delay


def main_sdm_loop(sweep_config: dict,
                  source_meter: SourcemeterBase,
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
    for v in voltages:
        print(f"\nAplicando voltaje: {v:.3f} V")
        source_meter.set_source_value(v)

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


def main():
    # carga del JSON para la configuracion
    with open("./config/config_measure.json", "r") as f:
        config = json.load(f)

    visa_config = config["Visa"]
    source_meter_config = config["Instruments"]["SourceMeter"]
    impedance_analyzer_config = config["Instruments"]["ImpedanceAnalyzer"]
    sweep_config = config["Sweep"]
    delay_config = config["Delays"]
    output_file_config = config["Results"]

    # Configura tu backend VISA
    visa = VisaResourceManager(backend=visa_config["backend"],
                               timeout_ms=visa_config["timeout_ms"])

    print("Recursos VISA:", visa.list_resources())

    # --- SourceMeter ---
    smu_res = visa.open(GPIB_ADDRESS_SOURCEMETER)
    smu = Keithley2400(smu_res, source_meter_config)

    # --- Impedance Analyzer ---
    imp_res = visa.open(GPIB_ADDRESS_IMPEDANCE_ANALYZER)
    imp_analyzer = KeysightE4990A(imp_res, impedance_analyzer_config)

    delay = get_delay(delay_config, callback_function=None)

    # init output file
    # Abrir fichero y escribir cabecera
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{output_file_config['File']['name']}_{timestamp}.csv"

    with open(file_name, mode="w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([h.strip() for h in output_file_config["File"]["header"].split(",")])

    # Ejecutar el bucle principal
    main_sdm_loop(sweep_config, smu, imp_analyzer, delay, file_name)


if __name__ == "__main__":
    main()
