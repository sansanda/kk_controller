from __future__ import annotations
from .base import ImpedanceAnalyzerBase
from typing import Dict, Any


class KeysightE4990A(ImpedanceAnalyzerBase):
    """
    TODO: Clase para reestructurar por completo. De momento no hay tiempo
    Implementación concreta para Keysight E4980A (subset SCPI).
    """

    def __init__(self, resource, config: Dict[str, Any], read_termination: str = "\n", write_termination: str = "\n"):
        """
        Inicializa el instrumento usando un diccionario de configuración.

        :param config: Diccionario con parámetros como:
                       {
                           "resource_name": "GPIB0::24::INSTR",
                           "timeout": 5000,
                           "init_output": False,
                           "source_mode": "current",
                           "source_value": 0.0,
                           "compliance": 10.0
                       }
        """
        super().__init__(resource)
        self.setup(config)

    def setup(self, config: Dict[str, Any]):
        """
        Configura el instrumento según los parámetros ya cargados en el init.
        """

        # Setup point-triggered sweep, Cs/Rs parameters, no DC bias.
        self.write("TRIG:SOUR BUS")
        self.write("INIT1:CONT ON")
        self.write("CALC1:PAR:COUN 3")
        self.write("CALC1:PAR1:DEF Z")
        self.write("CALC1:PAR2:DEF TZ")
        self.write("CALC1:PAR3:DEF CS")
        self.write("DISP:WIND1:SPL D1_2_3")

        self.write("SENS1:SWE:TYPE LIN")
        self.write(f"SENS1:FREQ:STAR {config['f_start']}")
        self.write(f"SENS1:FREQ:STOP {config['f_stop']}")
        self.write(f"SENS1:SWE:POIN {config['n_points']}")
        self.write(f"SOUR1:VOLT {config['vac_level']}")

        self.write("SOUR:BIAS:STAT OFF")

    def measure(self):
        """Read Cs and Rs traces, handle interleaved data correctly."""
        self.write("INIT1:CONT OFF")
        self.write("ABOR")  # aborts current measurement
        self.write("INIT1:CONT ON")
        self.write("TRIG:SING")  # trigger single
        self.query("*OPC?")

        self.write("FORM:DATA ASCII")
        self.write("CALC1:PAR1:SEL")
        self.write("CALC1:DATA:FDAT?")
        z_data = self.read()

        # Convertir la cadena en una lista de floats
        float_values = [float(val) for val in z_data.split(',')]

        # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
        z_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

        self.write("CALC1:PAR2:SEL")
        self.write("CALC1:DATA:FDAT?")
        phi_data = self.read()

        # Convertir la cadena en una lista de floats
        float_values = [float(val) for val in phi_data.split(',')]

        # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
        phi_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

        self.write("CALC1:PAR3:SEL")
        self.write("CALC1:DATA:FDAT?")
        cs_data = self.read()

        # Convertir la cadena en una lista de floats
        float_values = [float(val) for val in cs_data.split(',')]

        # Filtrar los valores en posiciones pares (0, 2, 4, ...) que no son cero
        cs_data = [val for i, val in enumerate(float_values) if i % 2 == 0 and val != 0.0]

        return z_data, phi_data, cs_data

    def preset(self) -> None:
        self.write("*RST")
        self.write(":STAT:PRES")

    def set_freq(self, hz: float) -> None:
        self.write(f":FREQ {hz}")

    def set_level_volt(self, v_rms: float) -> None:
        self.write(f":VOLT {v_rms}")

    def set_function(self, func: str = "CPD") -> None:
        # CPD = Capacitancia y factor de disipación
        self.write(f":FUNC:IMP {func}")

    def trigger_single(self) -> None:
        self.write(":INIT:IMM")
        self.write("*WAI")

    def fetch(self) -> tuple[float, float]:
        # Devuelve (param1, param2), p.ej. (C, D) para CPD
        resp = self.query(":FETC?").strip()
        a, b = resp.split(",")[:2]
        return float(a), float(b)
