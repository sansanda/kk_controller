from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any


class Modes(Enum):
    VOLTAGE_MODE = 'VOLT'
    CURRENT_MODE = 'CURR'
    AUTO_MODE = 'AUTO'


class Instrument(ABC):
    @abstractmethod
    def setup(self, settings: Dict[str, Any] = None) -> None:
        """
        Configures the Instrument with a dictionary of settings.
        Each implementation can interpret the settings as needed.
        """
        pass

    @abstractmethod
    def close(self) -> None: ...

class Multimeter(Instrument):

    @abstractmethod
    def measure(self) -> float:
        """Returns the measured current, volttage, resistance, etc...."""
        pass

    @abstractmethod
    def set_measure_range(self, _range: Any) -> None:
        """Sets the measurement range."""
        pass

    @abstractmethod
    def get_measure_range(self) -> float: ...

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

class Source(Instrument):

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


class ImpedanceAnalyzerBase(Instrument):
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
