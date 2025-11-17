from typing import Dict, Any

from devices import Instrument


class InstrumentsPort(Instrument):
    """
    Base genérica para instrumentos SCPI sobre VISA.
    Mantiene un `resource` PyVISA y helpers para SCPI.
    """

    def __init__(self, resource, settings: Dict[str, Any] = None):
        self._res = resource
        self.setup(settings)

    def setup(self, settings: Dict[str, Any] = None) -> None:
        if None: return
        self._res.read_termination = settings["VisaInstrument"]["read_termination"]
        self._res.write_termination = settings["VisaInstrument"]["write_termination"]

    # --- Helpers SCPI comunes ---
    def write(self, cmd: str) -> None:
        self._res.write(cmd)

    def query(self, cmd: str) -> str:
        return self._res.query(cmd)

    def read(self) -> str:
        return self._res.read()

    # --- Comandos SCPI estándar ---
    def idn(self) -> str:
        return self.query("*IDN?").strip()

    def reset(self) -> None:
        self.write("*RST")
        self.write("*CLS")

    def close(self) -> None:
        try:
            self._res.close()
        except Exception:
            pass

    # Context manager opcional
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
