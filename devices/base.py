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


class SourcemeterBase(VisaInstrument, ABC):
    """
    Interfaz abstracta de un SourceMeter (SMU).
    Implementa el contrato común, independientemente del modelo.
    """

    @abstractmethod
    def output(self, on: bool) -> None:
        """
        Activa o desactiva la salida del instrumento.

        Este método controla el estado de la salida del source_meter. Cuando se activa,
        el instrumento comienza a aplicar el valor configurado como fuente (voltaje o corriente).
        Cuando se desactiva, la salida se apaga.

        Parámetros:
            on (bool): Si es True, activa la salida. Si es False, la desactiva.

        Comando SCPI utilizado:
            ':OUTP ON' o ':OUTP OFF'
        """

    @abstractmethod
    def set_measure_function(self, mode: str):
        """
        Configura el modo de medición del Keithley 2410.

        Parámetros:
            mode (str): Modo de medición. Puede ser uno de los siguientes:
                        'VOLT', 'CURR', 'RES', 'V', 'C', 'R', 'I'

        Lanza:
            ValueError: Si el modo no es válido.
        """

    @abstractmethod
    def set_source_mode(self, mode: str) -> str:
        """
            Configura el modo de fuente (source) del SMU: corriente o tensión.

            Acepta alias:
                - corriente: 'current', 'curr', 'i'
                - tensión:   'voltage', 'volt', 'v'
        """

    @abstractmethod
    def get_source_mode(self) -> str:
        """
        Devuelve 'VOLT' o 'CURR' leyendo :SOUR:FUNC?.
        Acepta respuestas tipo 'VOLT' o 'VOLT:DC' (según FW).
        """

    @abstractmethod
    def set_measure_range(self, value: object) -> set[str]:
        """
        Configura el rango de medición del Keithley 2410 según la función activa.

        Parámetros:
            value (float | str): Valor del rango deseado o 'AUTO'/'A' para modo automático.

        Lanza:
            ValueError: Si el valor no es válido.
        """

    @abstractmethod
    def set_source_range(self, value: object) -> str:
        """
        Ajusta el rango de FUENTE para la función activa (VOLT o CURR).
        - 'auto'/'AUTO' -> habilita AUTO RANGE.
        - numérico -> fija rango y desactiva AUTO.
        Devuelve 'VOLT' o 'CURR' según la función de fuente afectada.

        SCPI:
            :SOUR:VOLT:RANG <val> / :SOUR:VOLT:RANG:AUTO ON|OFF
            :SOUR:CURR:RANG <val> / :SOUR:CURR:RANG:AUTO ON|OFF
        """

    @abstractmethod
    def set_source_value(self, value: float) -> str:
        """
        Establece el valor de la fuente según el modo actual (corriente o voltaje).

        Este método configura el valor de salida de la fuente dependiendo del modo
        de operación actual, que puede ser "current" (corriente) o "voltage" (voltaje).
        Utiliza el método `write` para enviar el comando SCPI correspondiente.

        Parámetros:
            value (float): El valor que se desea establecer en la fuente. Se interpreta
                           como corriente (amperios) o voltaje (voltios) según el modo.

        Retorna:
            str: El modo de fuente utilizado ("current" o "voltage").

        Lanza:
            RuntimeError: Si el modo de fuente no es soportado.
        """

    @abstractmethod
    def set_compliance(self, limit: float) -> str:
        """
        Ajusta la COMPLIANCE adecuada al modo de fuente:
          - Si Source V -> límite de corriente (A):  :SENS:CURR:PROT <value>
          - Si Source I -> límite de tensión (V):    :SENS:VOLT:PROT <value>
        """

    @abstractmethod
    def enable_remote_sense(self, enable: bool = True) -> None:
        """
        Activa/desactiva Remote Sense (4 hilos) en el instrumento (afecta V/Ω).
        """

    @abstractmethod
    def set_terminals(self, where: str = "FRONT") -> None:
        """
        Selecciona terminales FRONT o REAR.
        Recomendado: salida OFF antes de conmutar.
        """

    @abstractmethod
    def set_nplc(self, nplc: float) -> set[str]:
        """
        Ajusta el NPLC leyendo primero la(s) función(es) de medida activas en el instrumento.
        Aplica el mismo NPLC a todas las funciones activas (útil en modo concurrente).
        Devuelve el conjunto de funciones a las que se aplicó NPLC.

        SCPI (serie 2400/2410):
            - :SENS:VOLT:NPLC <n>
            - :SENS:CURR:NPLC <n>
            - :SENS:RES:NPLC  <n>     (ohmios 2 hilos)
            - :SENS:FRES:NPLC <n>     (ohmios 4 hilos)
        """

    @abstractmethod
    def get_measure_function(self) -> str:
        """
            Consulta la función de medición activa del instrumento.

            Este método envía el comando SCPI ':SENS:FUNC?' al instrumento para obtener
            la función de medida actual (por ejemplo, 'VOLT:DC', 'CURR:DC', etc.). Luego
            procesa la respuesta para extraer la parte principal ('VOLT', 'CURR', 'RES').

            Retorna:
                str: La función de medida activa ('VOLT', 'CURR' o 'RES').

            Lanza:
                RuntimeError: Si la respuesta no contiene ninguna de las funciones válidas.
            """

    @abstractmethod
    def configure_data_format_elements(self, elements: [str]) -> None:
        """
        Configura los elementos del formato de datos que el Keithley 2410 devolverá en las lecturas.

        Parámetros:
            elements (list[str]): Lista de elementos válidos para el formato de datos.
                                  Ejemplos comunes: 'READ', 'VOLT', 'CURR', 'RES', 'TIME', 'STAT'

        Lanza:
            ValueError: Si la lista está vacía o contiene elementos no válidos.
        """


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


class AmmeterBase(ABC):
    @abstractmethod
    def measure_current(self) -> float:
        """Returns the measured current in amperes."""
        pass

    @abstractmethod
    def set_ammeter_range(self, range_in_amps: Any) -> None:
        """Sets the measurement range of the ammeter."""
        pass

    @abstractmethod
    def configure_ammeter(self, settings: Dict[str, Any] = None) -> None:
        """
        Configures the ammeter with a dictionary of settings.
        Each implementation can interpret the settings as needed.
        """
        pass


class VoltmeterBase(ABC):
    @abstractmethod
    def measure_voltage(self) -> float:
        """Returns the measured voltage in volts."""
        pass

    @abstractmethod
    def set_voltmeter_range(self, range_in_volts: Any) -> None:
        """Sets the measurement range of the voltmeter."""
        pass

    @abstractmethod
    def configure_voltmeter(self, settings: Dict[str, Any] = None) -> None:
        """
        Configures the voltmeter with a dictionary of settings.
        Each implementation can interpret the settings as needed.
        """
        pass
