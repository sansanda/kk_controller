from __future__ import annotations
from abc import ABC, abstractmethod


class VisaInstrument(ABC):
    """
    Base genérica para instrumentos SCPI sobre VISA.
    Mantiene un `resource` PyVISA y helpers para SCPI.
    """

    def __init__(self, resource, read_termination: str = "\n", write_termination: str = "\n"):
        self._res = resource
        self._res.read_termination = read_termination
        self._res.write_termination = write_termination

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


class SourcemeterBase(VisaInstrument, ABC):
    """
    Interfaz abstracta de un SourceMeter (SMU).
    Implementa el contrato común, independientemente del modelo.
    """

    @abstractmethod
    def output(self, on: bool) -> None: ...

    @abstractmethod
    def set_source_mode(self, mode: str) -> str: ...

    @abstractmethod
    def set_measure_voltage(self) -> float: ...

    @abstractmethod
    def set_measure_current(self) -> float: ...

    @abstractmethod
    def set_measure_range(self, range_or_auto: object) -> set[str]: ...

    @abstractmethod
    def set_source_range(self, range_or_auto: object) -> str: ...

    @abstractmethod
    def set_source_value(self, value: float) -> str: ...

    @abstractmethod
    def set_compliance(self, limit: float) -> str: ...

    @abstractmethod
    def enable_remote_sense(self, enable: bool = True) -> None: ...

    @abstractmethod
    def set_terminals(self, where: str = "FRONT") -> None: ...


class ImpedanceAnalyzerBase(VisaInstrument, ABC):
    """
    Interfaz abstracta de un Analizador de Impedancias.
    """

    @abstractmethod
    def preset(self) -> None: ...

    @abstractmethod
    def set_freq(self, hz: float) -> None: ...

    @abstractmethod
    def set_level_volt(self, v_rms: float) -> None: ...

    @abstractmethod
    def set_function(self, func: str) -> None: ...

    @abstractmethod
    def trigger_single(self) -> None: ...

    @abstractmethod
    def fetch(self) -> tuple[float, float]: ...


class VisaInstrument(ABC):
    """
    Base genérica para instrumentos SCPI sobre VISA.
    Mantiene un `resource` PyVISA y helpers para SCPI.
    """

    def __init__(self, resource, read_termination: str = "\n", write_termination: str = "\n"):
        self._res = resource
        self._res.read_termination = read_termination
        self._res.write_termination = write_termination

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
