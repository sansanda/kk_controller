from __future__ import annotations
from .base import ImpedanceAnalyzerBase


class KeysightE4990A(ImpedanceAnalyzerBase):
    """
    TODO: Clase inservible. Por lo pronto
    Implementación concreta para Keysight E4980A (subset SCPI).
    """

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
