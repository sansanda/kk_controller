from __future__ import annotations

import atexit

import pyvisa.errors

from communications.CommunicationPorts import InstrumentsPort
from .base import ImpedanceAnalyzerBase
from typing import Dict, Any


class KeysightE4990A(ImpedanceAnalyzerBase):
    """
    TODO: Clase para reestructurar por completo. De momento no hay tiempo
    Implementación concreta para Keysight E4980A (subset SCPI).
    """

    def __init__(self, resource, settings: Dict[str, Any], read_termination: str = "\n", write_termination: str = "\n"):
        """
        Inicializa el instrumento usando un diccionario de configuración.

        :param settings: Diccionario con parámetros como:
                       {
                           "resource_name": "GPIB0::24::INSTR",
                           "timeout": 5000,
                           "init_output": False,
                           "source_mode": "current",
                           "source_value": 0.0,
                           "compliance": 10.0
                       }
        """
        self._port = InstrumentsPort(resource, None)
        self.setup(settings)
        atexit.register(self.close)

    def setup(self, settings: Dict[str, Any] = None) -> None:
        """
        Configura el instrumento según los parámetros ya cargados en el init.
        """
        # Setup point-triggered sweep, Cs/Rs parameters, no DC bias.
        self._port.write("TRIG:SOUR BUS")
        self._port.write("INIT1:CONT ON")
        self._port.write("CALC1:PAR:COUN 3")
        self._port.write("CALC1:PAR1:DEF Z")
        self._port.write("CALC1:PAR2:DEF TZ")
        self._port.write("CALC1:PAR3:DEF CS")
        self._port.write("DISP:WIND1:SPL D1_2_3")

        self._port.write("SENS1:SWE:TYPE LIN")
        self._port.write(f"SENS1:FREQ:STAR {settings['f_start']}")
        self._port.write(f"SENS1:FREQ:STOP {settings['f_stop']}")
        self._port.write(f"SENS1:SWE:POIN {settings['n_points']}")
        self._port.write(f"SOUR1:VOLT {settings['vac_level']}")

        self._port.write("SOUR:BIAS:STAT OFF")

    def measure(self):
        """Read Cs and Rs traces, handle interleaved data correctly."""
        self._port.write("INIT1:CONT OFF")
        self._port.write("ABOR")  # aborts current measurement
        self._port.write("INIT1:CONT ON")
        self._port.write("TRIG:SING")  # trigger single
        self._port.query("*OPC?")

        self._port.write("FORM:DATA ASCII")
        self._port.write("CALC1:PAR1:SEL")
        self._port.write("CALC1:DATA:FDAT?")
        z_data = self._port.read()

        # Convertir la cadena en una lista de floats
        float_values = [float(val) for val in z_data.split(',')]

        # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
        z_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

        self._port.write("CALC1:PAR2:SEL")
        self._port.write("CALC1:DATA:FDAT?")
        phi_data = self._port.read()

        # Convertir la cadena en una lista de floats
        float_values = [float(val) for val in phi_data.split(',')]

        # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
        phi_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

        self._port.write("CALC1:PAR3:SEL")
        self._port.write("CALC1:DATA:FDAT?")
        cs_data = self._port.read()

        # Convertir la cadena en una lista de floats
        float_values = [float(val) for val in cs_data.split(',')]

        # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
        cs_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

        return z_data, phi_data, cs_data

    def preset(self) -> None:
        self._port.write("*RST")
        self._port.write(":STAT:PRES")

    def set_freq(self, hz: float) -> None:
        self._port.write(f":FREQ {hz}")

    def set_level_volt(self, v_rms: float) -> None:
        self._port.write(f":VOLT {v_rms}")

    def set_function(self, func: str = "CPD") -> None:
        # CPD = Capacitancia y factor de disipación
        self._port.write(f":FUNC:IMP {func}")

    def trigger_single(self) -> None:
        self._port.write(":INIT:IMM")
        self._port.write("*WAI")

    def fetch(self) -> tuple[float, float]:
        # Devuelve (param1, param2), p.ej. (C, D) para CPD
        resp = self._port.query(":FETC?").strip()
        a, b = resp.split(",")[:2]
        return float(a), float(b)

    def close(self):
        print("Apagando y cerrando instrumento E4990A...")
        try:
            self._port.close()
        except pyvisa.errors.InvalidSession:
            print("Puerto ya cerrado")

