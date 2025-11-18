from typing import Dict, Any
from devices.base import Instrument


class InstrumentsPort(Instrument):
    """
    Wrapper genérico para un recurso VISA, GPIB, RS232 u otro tipo de
    comunicación SCPI, proporcionando utilidades comunes para escribir y leer
    comandos, así como las funciones SCPI estándar.

    Esta clase sirve como base para implementar puertas de comunicación hacia
    instrumentos de medida. No interpreta comandos específicos de un modelo:
    únicamente envía y recibe texto SCPI, y expone métodos básicos como
    ``*IDN?`` o ``*RST``.

    Parameters
    ----------
    resource : Any
        Objeto de recurso bajo nivel (por ejemplo, un handler de PyVISA o un
        wrapper RS232) que implemente los métodos `write()`, `read()` y `query()`.
    settings : Dict[str, Any], optional
        Opcionalmente, configuración inicial que puede ser procesada durante
        `setup()`. La clase base no la usa directamente.
    """

    def __init__(self, resource, settings: Dict[str, Any] = None):
        self._res = resource
        # self.setup(settings)

    def setup(self, settings: Dict[str, Any] = None) -> None:
        """
        Configura el instrumento o puerto de comunicación.

        Este método debe ser implementado por clases hijas si necesitan procesar
        parámetros de configuración inicial (por ejemplo: terminadores, timeouts,
        modos, o ajustes específicos del backend de comunicación).

        Parameters
        ----------
        settings : Dict[str, Any], optional
            Diccionario de configuración. El contenido depende de la
            implementación concreta.

        Raises
        ------
        NotImplemented
            Si la clase hija no sobrescribe este método.
        """
        raise NotImplemented

    # --- Helpers SCPI comunes ---
    def write(self, cmd: str) -> None:
        """
        Envía un comando SCPI al instrumento sin esperar respuesta.

        Parameters
        ----------
        cmd : str
            Comando SCPI a enviar (por ejemplo: ``"VOLT 1.0"``).
        """
        self._res.write(cmd)

    def query(self, cmd: str) -> str:
        """
        Envía un comando SCPI y devuelve la respuesta del instrumento.

        Parameters
        ----------
        cmd : str
            Comando SCPI a enviar, normalmente terminado en signo de pregunta
            (por ejemplo: ``"MEAS:VOLT?"``).

        Returns
        -------
        str
            Respuesta del instrumento como cadena.
        """
        return self._res.query(cmd)

    def read(self) -> str:
        """
        Lee una respuesta pendiente del instrumento.

        Returns
        -------
        str
            Texto recibido del instrumento.
        """
        return self._res.read()

    # --- Comandos SCPI estándar ---
    def idn(self) -> str:
        """
        Devuelve la identificación del instrumento usando el comando estándar SCPI ``*IDN?``.

        Returns
        -------
        str
            Cadena con la identificación del instrumento (fabricante, modelo,
            número de serie y versión de firmware).
        """
        return self.query("*IDN?").strip()

    def reset(self) -> None:
        """
        Reinicia el instrumento a sus valores por defecto y limpia los buffers
        de estado.

        Envía los comandos SCPI estándar:
        - ``*RST`` : Reinicio del instrumento
        - ``*CLS`` : Limpieza del registro de estado
        """
        self.write("*RST")
        self.write("*CLS")

    def close(self) -> None:
        """
        Cierra la conexión con el recurso subyacente.

        Si el recurso lanza una excepción al cerrar, se ignora silenciosamente
        para evitar interrupciones.
        """
        try:
            self._res.close()
        except Exception:
            pass

    # Context manager opcional
    def __enter__(self):
        """
        Permite usar la clase como context manager con ``with``.

        Returns
        -------
        InstrumentsPort
            La propia instancia para encadenamiento de métodos.
        """
        return self

    # def __exit__(self, exc_type, exc, tb):
    #     """
    #     Cierra automáticamente el recurso al salir del bloque ``with``.
    #
    #     Parameters
    #     ----------
    #     exc_type : type or None
    #         Tipo de excepción si se produjo una dentro del bloque.
    #     exc : Exception or None
    #         Instancia de la excepción.
    #     tb : traceback or None
    #         Traza de la excepción.
    #     """
    #     self.close()
