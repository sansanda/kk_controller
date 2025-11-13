from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any


class Modes(Enum):
    VOLTAGE_MODE = 'VOLT'
    CURRENT_MODE = 'CURR'
    AUTO_MODE = 'AUTO'


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


class Multimeter(ABC):

    @abstractmethod
    def setup_multimeter(self, settings: Dict[str, Any] = None) -> None:
        """
        Configures the multimeter with a dictionary of settings.
        Each implementation can interpret the settings as needed.
        """
        pass

    @abstractmethod
    def measure(self) -> float:
        """Returns the measured current, volttage, resistance, etc...."""
        pass

    @abstractmethod
    def set_measure_range(self, _range: Any) -> None:
        """Sets the measurement range."""
        pass

    @abstractmethod
    def set_measure_function(self, function: str) -> None:
        """
        Sets the function to measure: can be voltage_dc, current_dc, resistance,etc.
        """
        pass

    @abstractmethod
    def get_measure_function(self) -> str:
        """Gets the actual selected function
        :return str with thw actual selected function
        """
        pass

class Source(ABC):

    @abstractmethod
    def setup_source(self, settings: Dict[str, Any] = None) -> None:
        """
        Configures the multimeter with a dictionary of settings.
        Each implementation can interpret the settings as needed.
        """
        pass

    @abstractmethod
    def set_source_range(self, range_or_auto: str = "AUTO") -> str:
        """

        :param range_or_auto:
        :return:
        """

    @abstractmethod
    def get_source_range(self) -> float:
        """

        :return:
        """

    @abstractmethod
    def set_source_mode(self, mode: str) -> str:
        """

        :param mode:
        :return:
        """

    @abstractmethod
    def get_source_mode(self) -> Modes:
        """

        :return:
        """

    @abstractmethod
    def set_source_value(self, value: float) -> str:
        """

        :param value:
        :return:
        """

    @abstractmethod
    def get_source_value(self) -> float:
        """

        :return:
        """

    @abstractmethod
    def set_compliance(self, limit: float) -> None:
        """

        :param limit:
        :return:
        """

    @abstractmethod
    def get_compliance(self) -> float:
        """

        :return:
        """

    @abstractmethod
    def set_nplc(self, nplc: float) -> None:
        """

        :param nplc:
        :return:
        """

    @abstractmethod
    def get_nplc(self) -> float:
        """

        :return:
        """

    def set_terminals(self, where: str = "FRONT") -> None:
        """

        :param where:
        :return:
        """

    @abstractmethod
    def get_terminals(self) -> str:
        """

        :return:
        """

    @abstractmethod
    def output(self, on: bool) -> None:
        """

        :param on:
        :return:
        """

class SourcemeterBase(VisaInstrument, Source, Multimeter, ABC):
    """
    Interfaz abstracta de un SourceMeter (SMU).
    Implementa el contrato común, independientemente del modelo.
    """
    pass


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
