import threading
import time
from typing import Callable
from enum import Enum
from abc import ABC, abstractmethod

from utils.data_structures.lists import LimitedList
from utils.my_statistics import my_statistics


class DelayType(Enum):
    __version__ = "1.0.0"
    TIME = "time"
    STATISTICS = "statistics"


class DelayState(Enum):
    __version__ = "1.0.0"
    INITIATED = 'initiated'
    STARTED = 'started'
    PAUSED = 'paused'


class Delay(ABC):
    __version__ = "1.0.0"

    @abstractmethod
    def start(self): pass

    @abstractmethod
    def pause(self): pass

    @abstractmethod
    def resume(self): pass

    @abstractmethod
    def reset(self): pass

    @abstractmethod
    def elapsed(self) -> float: pass

    @abstractmethod
    def remaining(self) -> float: pass


class DelayFactory:
    __version__ = "1.0.1"
    """Factory Registry para crear instancias de Delay dinámicamente."""

    _registry = {}  # type: dict[str, type]

    @classmethod
    def register_delay(cls, key, delay_class):
        """Registra una clase de delay bajo una clave única."""
        cls._registry[key] = delay_class

    @classmethod
    def create_delay(cls, delay_type, **kwargs):
        """Crea una instancia del delay solicitado."""
        key = delay_type.value if isinstance(delay_type, DelayType) else delay_type
        delay_class = cls._registry.get(key)

        if not delay_class:
            raise ValueError(f"No hay delay registrado para '{key}'")

        return delay_class(**kwargs)

    @classmethod
    def available_delays(cls):
        """Devuelve una lista de tipos registrados."""
        return list(cls._registry.keys())


class TimeDelay(Delay):
    __version__ = "1.0.1"

    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self.timer = threading.Timer(timeout, callback)
        self.startedTime = None  # solo para iniciar
        self.pausedTime = None  # solo para iniciar
        self.state = 'initiated'

    def start(self):
        """
        Inicia el timer y la cuenta atras.
        :return: None
        """
        if not self.state == 'started':
            self.state = 'started'
            self.startedTime = time.time()
            self.timer.start()

    def pause(self):
        """
        Pone el timer en modo pause conservando los valores de remaining time y elapsed time.
        :return: None
        """
        if self.state == 'initiated':
            return
        self.timer.cancel()
        self.pausedTime = time.time()
        self.state = 'paused'

    def resume(self):
        """
        Reanuda el timer si es que previamente se había ejecutado pause.
        :return: None
        """
        if not self.state == 'paused':
            return
        self.timer = threading.Timer(
            self.timeout - (self.pausedTime - self.startedTime),
            self.callback)
        self.timer.start()
        self.state = 'started'

    def reset(self):
        """
        Reinicia el timer a los valores de constructor.
        Ojo. El timer se detiene despues de hacer un reset y se reinician los valores de timeout, remaining y elapsed.
        Remaining time  = timeout, elapsed time = 0s.
        Es necesario volver a hacer un start del timer.
        :return: None
        """
        self.timer.cancel()
        self.__init__(self.timeout, self.callback)

    def elapsed(self):
        """
        Tiempo transcurrido (en segundos) del timeout inicial.
        Ojo, los eventos como pause hace parar la cuenta del tiempo transcurrido, como es de esperar.
        :return: tiempo (en segundos) que queda para finalizar el timeout
        """
        return self.timeout - self.remaining()

    def remaining(self):
        """
        Devuelve el tiempo (en segundos) que queda para finalizar el timeout y llamar a la función de callback
        :return: tiempo (en segundos) que queda para finalizar el timeout
        """
        if not self.startedTime:
            return self.timeout
        else:
            # se ha iniciado alguna vez el timer
            if not self.pausedTime:
                # pero nunca se ha pausado
                return self.timeout - (time.time() - self.startedTime)
            else:
                # se ha iniciado y se ha pausado alguna ves el timer
                return self.timeout - (self.pausedTime - self.startedTime)

    def __str__(self):
        callback_name = getattr(self.callback, '__name__', repr(self.callback))
        return (f"TimeDelay(timeout={self.timeout:.2f}s, state='{self.state}', "
                f"elapsed={self.elapsed():.2f}s, remaining={self.remaining():.2f}s, "
                f"callback={callback_name})")


class SyncrhonTimeDelay(Delay):
    __version__ = "1.0.0"

    def __init__(self, timeout):
        self.timeout = timeout
        self.timer = threading.Timer(timeout, self.callback)
        self.startedTime = None  # solo para iniciar
        self.pausedTime = None  # solo para iniciar
        self.state = 'initiated'

    def start(self):
        """
        Inicia el timer y la cuenta atras.
        :return: None
        """
        if not self.state == 'started':
            self.state = 'started'
            self.startedTime = time.time()
            self.timer.start()

    def pause(self):
        """
        Pone el timer en modo pause conservando los valores de remaining time y elapsed time.
        :return: None
        """
        if self.state == 'initiated':
            return
        self.timer.cancel()
        self.pausedTime = time.time()
        self.state = 'paused'

    def resume(self):
        """
        Reanuda el timer si es que previamente se había ejecutado pause.
        :return: None
        """
        if not self.state == 'paused':
            return
        self.timer = threading.Timer(
            self.timeout - (self.pausedTime - self.startedTime),
            self.callback)
        self.timer.start()
        self.state = 'started'

    def reset(self):
        """
        Reinicia el timer a los valores de constructor.
        Ojo. El timer se detiene despues de hacer un reset y se reinician los valores de timeout, remaining y elapsed.
        Remaining time  = timeout, elapsed time = 0s.
        Es necesario volver a hacer un start del timer.
        :return: None
        """
        self.timer.cancel()
        self.__init__(self.timeout)

    def elapsed(self):
        """
        Tiempo transcurrido (en segundos) del timeout inicial.
        Ojo, los eventos como pause hace parar la cuenta del tiempo transcurrido, como es de esperar.
        :return: tiempo (en segundos) que queda para finalizar el timeout
        """
        return self.timeout - self.remaining()

    def remaining(self):
        """
        Devuelve el tiempo (en segundos) que queda para finalizar el timeout y llamar a la función de callback
        :return: tiempo (en segundos) que queda para finalizar el timeout
        """
        if not self.startedTime:
            return self.timeout
        else:
            # se ha iniciado alguna vez el timer
            if not self.pausedTime:
                # pero nunca se ha pausado
                return self.timeout - (time.time() - self.startedTime)
            else:
                # se ha iniciado y se ha pausado alguna ves el timer
                return self.timeout - (self.pausedTime - self.startedTime)

    def callback(self):
        while True:
            if self.state == 'done':
                return

    def __str__(self):
        callback_name = getattr(self.callback, '__name__', repr(self.callback))
        return (f"TimeDelay(timeout={self.timeout:.2f}s, state='{self.state}', "
                f"elapsed={self.elapsed():.2f}s, remaining={self.remaining():.2f}s, "
                f"callback={callback_name})")


class StatisticsDelay(Delay):
    __version__ = "1.0.1"
    """
    Clase que implementa un delay basado en estadísticas sobre valores leídos periódicamente.

    Cada cierto intervalo de tiempo (timer_interval), se lee un valor usando la función
    inyectada `read_value()`. Se calcula una métrica (último valor, media o desviación estándar)
    y se compara con un valor de referencia usando un comparador (mayor, menor, igual).

    Si la condición se cumple, se ejecuta el callback y opcionalmente se limpia la lista de valores.

    La lista de valores mantiene como máximo los últimos 120 elementos usando `LimitedList`.
    Todas las operaciones sobre la lista son thread-safe gracias a un lock interno.
    """

    def __init__(self,
                 reference_value: float,
                 metric: my_statistics.Metrics,
                 comparator: my_statistics.Comparator,
                 timer_interval: float,
                 callback: Callable[[], None],
                 read_value: Callable[[], float]):
        """
        Inicializa el delay estadístico.

        Args:
            reference_value (float): Valor de referencia para la comparación.
            metric (my_statistics.Metrics): Métrica a calcular sobre los valores (LAST_VALUE, MEAN, ST_DEV).
            comparator (my_statistics.Comparator): Comparador que determina cuándo disparar el callback.
            timer_interval (float): Intervalo en segundos entre lecturas de valores.
            callback (Callable[[], None]): Función a ejecutar cuando se cumpla la condición.
            read_value (Callable[[], float]): Función que devuelve un valor numérico a añadir a la lista.
        """
        self.reference_value = reference_value
        self.metric = metric
        self.comparator = comparator
        self.timer_interval = timer_interval
        self.callback = callback
        self.read_value = read_value  # inyección de dependencia

        self.values = LimitedList(120)  # lista de valores con longitud máxima 120
        self.timer = TimeDelay(self.timer_interval, self._timer_task)
        self.started_time = None

        # Lock para operaciones thread-safe sobre la lista
        self._values_lock = threading.Lock()

    def start(self):
        """Inicia el timer y comienza a leer valores periódicamente."""
        self.started_time = time.time()
        self.timer.start()

    def pause(self):
        """Pausa el timer conservando el tiempo transcurrido."""
        self.timer.pause()

    def resume(self):
        """Reanuda el timer después de una pausa."""
        self.timer.resume()

    def reset(self):
        """Reinicia el timer y borra el tiempo transcurrido del estado actual."""
        self.timer.reset()

    def elapsed(self) -> float:
        """
        Devuelve el tiempo transcurrido desde que se llamó a `start()`.

        Returns:
            float: Tiempo en segundos transcurrido desde `start()`. 0 si no se ha iniciado.
        """
        if not self.started_time:
            return 0.0
        return time.time() - self.started_time

    def remaining(self) -> float:
        """
        Devuelve el tiempo restante hasta que se dispare el timer.

        Returns:
            float: Tiempo en segundos restante. None si no implementado.
        """
        pass

    def _timer_task(self) -> None:
        """
        Función interna llamada por el timer en cada tick.
        - Añade un valor a la lista de forma thread-safe.
        - Calcula la métrica seleccionada.
        - Comprueba si la condición se cumple usando el comparador.
        - Ejecuta el callback si se cumple y limpia la lista de valores.
        - Reinicia el timer si no se cumple la condición.
        """
        with self._values_lock:
            self.values.append(self.read_value())
            trigger = my_statistics.check_match(
                my_statistics.compute_metric(self.values, self.metric),
                self.comparator,
                self.reference_value
            )

        if trigger:
            self.values.clear()
            self.callback()
        else:
            self.timer.reset()
            self.timer.start()

    def clear_values(self) -> None:
        """
        Limpia la lista de valores de manera segura (thread-safe).

        Esto puede usarse para reiniciar manualmente la ventana de valores.
        """
        with self._values_lock:
            self.values.clear()

# 🧪 Ejemplo de registro dinámico
#
# Supón que creas un nuevo tipo de delay:
#
# class CustomDelay:
#     def __init__(self, message):
#         self.message = message
#
#     def start(self):
#         print(f"Starting custom delay: {self.message}")
#
#
# Puedes registrarlo en cualquier momento:
#
# from utils.delays.delays import DelayFactory
#
# DelayFactory.register_delay("custom", CustomDelay)
#
# d = DelayFactory.create_delay("custom", message="hola mundo")
# d.start()
#
#
# Salida:
#
# Starting custom delay: hola mundo

# ✅ Ventajas de este enfoque
# Característica	Beneficio
# Registro centralizado	Evita modificar la factoría para nuevos tipos
# Flexible	Puedes registrar clases dinámicamente en tests, plugins, etc.
# Limpio	Los tests no importan clases concretas
# Extensible	Perfecto para proyectos donde se añadan nuevos delays
