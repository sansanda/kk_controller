import threading
import time
from typing import Callable, Optional
from enum import Enum
from abc import ABC, abstractmethod

from utils.data_structures.lists import LimitedList
from utils.my_statistics import my_statistics


class DelayType(Enum):
    __version__ = "1.0.0"
    TIME = "TimeDelay"
    STATISTICS = "StatisticsDelay"


class DelayState(Enum):
    __version__ = "1.0.0"
    INITIATED = 'initiated'
    STARTED = 'started'
    PAUSED = 'paused'
    DONE = 'done'
    CONTINUE = 'continue'


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
    def is_done(self) -> bool: pass

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
    __version__ = "1.0.5"
    """
    Implementa un temporizador configurable con soporte para pausa, reanudación,
    reinicio y ejecución repetida mediante un número definido de disparos (n_shots).

    Esta clase encapsula un `threading.Timer` y añade control de estado, permitiendo
    iniciar, pausar, reanudar o reiniciar el temporizador sin perder el tiempo restante.
    Puede ejecutar una función de callback al finalizar cada disparo o solo al completar
    el último, dependiendo del flujo configurado.

    Estados posibles:
        - 'initiated' : El temporizador ha sido creado, pero no ha comenzado.
        - 'started'   : El temporizador está en ejecución.
        - 'paused'    : El temporizador está pausado.
        - 'done'      : El temporizador ha completado todos los disparos.

    Atributos:
        timeout (float): Tiempo (en segundos) de cada disparo del temporizador.
        callback (Callable | None): Función que se ejecuta al finalizar el último disparo.
        n_shots (int): Número total de disparos del temporizador. Si es <= 0, se fuerza a 1.
        remaining_shots (int): Disparos restantes antes de finalizar el ciclo completo.
        timer (threading.Timer): Instancia interna del temporizador.
        startedTime (float | None): Marca temporal del inicio del último disparo.
        pausedTime (float | None): Marca temporal del momento en que se pausó.
        state (str): Estado actual del temporizador.

    Métodos principales:
        start()  -> None:
            Inicia el temporizador o lo reanuda si estaba pausado.
            Si el temporizador estaba en estado 'done', se reinicia antes de iniciar.

        pause()  -> None:
            Pausa el temporizador, conservando el tiempo restante y transcurrido.

        resume() -> None:
            Reanuda la cuenta regresiva desde el punto donde se pausó.

        reset()  -> None:
            Restablece el temporizador a su estado inicial, con el número total
            de disparos reiniciado. El temporizador queda detenido.

        is_done() -> bool:
            Devuelve True si el temporizador ha completado todos los disparos.

        elapsed() -> float:
            Devuelve el tiempo total transcurrido desde el inicio, en segundos.

        remaining() -> float:
            Devuelve el tiempo restante (en segundos) hasta completar todos los disparos.

    Ejemplo:
        >>> import time
        >>> def fin():
        ...     print("¡Finalizado!")
        ...
        >>> t = TimeDelay(timeout=2.0, callback=fin, n_shots=3)
        >>> t.start()
        >>> time.sleep(3)
        >>> t.pause()
        >>> print("Pausado:", t.remaining())
        >>> t.resume()
        >>> # Tras 6 segundos aprox. se imprimirá "¡Finalizado!"
    """

    def __init__(self, timeout=1.0, callback=None, n_shots=1):
        """
        Inicializa el temporizador.

        Args:
            timeout (float): Tiempo de cada disparo en segundos.
            callback (Callable | None): Función que se ejecuta al finalizar el último disparo.
            n_shots (int): Número total de disparos del temporizador.
        """
        self.timeout = timeout
        self.callback = callback
        self.n_shots = n_shots
        if not self.n_shots or self.n_shots < 0:
            self.n_shots = 1
        self.remaining_shots = self.n_shots
        self.timer = threading.Timer(timeout, self._internal_callback)
        self.startedTime = None  # solo para iniciar
        self.pausedTime = None  # solo para iniciar
        self.state = DelayState.INITIATED

    def start(self):
        """
        Inicia el temporizador o lo reanuda si estaba pausado.
        Si el temporizador estaba en estado 'done', se reinicia antes de iniciar.
        """
        if self.state == DelayState.STARTED: return
        if self.state in (DelayState.INITIATED, DelayState.PAUSED, DelayState.DONE):
            if self.state == DelayState.PAUSED:
                self.timer = threading.Timer(
                    self.timeout - (self.pausedTime - self.startedTime),
                    self._internal_callback)
            if self.state == DelayState.DONE:
                # si el timer ha finalizado entonces debemos rehacerlo antes de volver a hacer un start
                self.reset()
            self.state = DelayState.STARTED
            self.startedTime = time.time()
            self.timer.start()

    def pause(self):
        """
        Pausa el temporizador, conservando el tiempo restante y transcurrido.
        """
        if not self.state == DelayState.STARTED: return
        self.state = DelayState.PAUSED
        self.timer.cancel()
        self.pausedTime = time.time()

    def resume(self):
        """
        Reanuda el temporizador desde donde se pausó.
        """
        if not self.state == DelayState.PAUSED:
            return
        self.start()

    def reset(self):
        """
        Reinicia el temporizador a los valores iniciales.

        Restablece remaining_shots al número original de disparos y rearma
        el temporizador. No inicia automáticamente; es necesario llamar a start().
        """
        self.remaining_shots = self.n_shots
        self._rearm()  # Rearma el temporizador

    def is_done(self) -> bool:
        """
        Comprueba si el temporizador ha completado todos los disparos.

        Returns:
            bool: True si el temporizador está en estado 'done'.
        """
        return self.state == DelayState.DONE

    def elapsed(self):
        """
        Devuelve el tiempo total transcurrido desde el inicio del temporizador
        hasta el momento actual, considerando pausas.

        Returns:
            float: Tiempo transcurrido en segundos.
        """
        return self.timeout * self.n_shots - self.remaining()

    def remaining(self):
        """
        Devuelve el tiempo restante hasta completar todos los disparos.

        Returns:
            float: Tiempo restante en segundos.
        """
        if not self.startedTime:
            return self.timeout * self.n_shots
        else:
            # se ha iniciado alguna vez el timer
            if not self.pausedTime:
                # pero nunca se ha pausado
                # (self.timeout - (time.time() - self.startedTime) es el tiempo que queda de un timeout
                return self.timeout * self.remaining_shots + (self.timeout - (time.time() - self.startedTime))
            else:
                # se ha iniciado y se ha pausado alguna vez el timer
                return self.timeout * self.remaining_shots + (self.timeout - (self.pausedTime - self.startedTime))

    def _internal_callback(self):
        """
        Callback interno llamado por threading.Timer al expirar cada disparo.

        Reduce remaining_shots y, si no ha terminado, rearma y reinicia el timer.
        Llama a la función callback del usuario si se completan todos los disparos.
        """
        self.remaining_shots = self.remaining_shots - 1
        if self.remaining_shots == 0:
            self.state = DelayState.DONE
        else:
            # aqui, rearmar el timer y hacer un start
            self._rearm()
            self.start()
        # if self.state = 'done'
        if self.state == DelayState.DONE and self.callback:
            self.callback()

    def _rearm(self):
        """
        Rearma el temporizador sin reinicializar todo el objeto.

        Cancela cualquier timer activo y prepara uno nuevo.
        """
        if self.timer.is_alive(): self.timer.cancel()
        self.timer = threading.Timer(self.timeout, self._internal_callback)
        self.startedTime = None
        self.pausedTime = None
        self.state = DelayState.INITIATED

    def __str__(self):
        """
        Representación en cadena del objeto, mostrando estado, tiempos y callback.

        Returns:
            str: Información resumida del temporizador.
        """
        callback_name = getattr(self.callback, '__name__', repr(self.callback))
        return (f"TimeDelay(timeout={self.timeout:.2f}s, state='{self.state.value}', "
                f"elapsed={self.elapsed():.2f}s, remaining={self.remaining():.2f}s, "
                f"callback={callback_name}, n_shots={self.n_shots})")


class StatisticsDelay(Delay):
    __version__ = "1.0.3"

    """
    Clase que implementa un delay basado en estadísticas sobre valores leídos periódicamente.

    Cada cierto intervalo de tiempo (timer_interval), se lee un valor usando la función
    inyectada `read_value()`. Se calcula una métrica (último valor, media o desviación estándar)
    y se compara con un valor de referencia usando un comparador (mayor, menor, igual).

    Si la condición se cumple, se ejecuta el callback y opcionalmente se limpia la lista de valores.

    La lista de valores mantiene como máximo los últimos 120 elementos usando `LimitedList`.
    Todas las operaciones sobre la lista son thread-safe gracias a un lock interno.
    """

    # TODO: para el caso de metricas como stdev, mean hay que asegurar que el delay comparé solo a partir de n numero, para evitar un match prematuro
    def __init__(self,
                 reference_value: float,
                 metric: my_statistics.Metrics,
                 comparator: my_statistics.Comparator,
                 timer_interval: float,
                 read_value: Callable[[], float],
                 callback: Optional[Callable[[], None]] = None
                 ):
        """
        Inicializa el delay estadístico.

        Args:
            reference_value (float): Valor de referencia para la comparación.
            metric (my_statistics.Metrics): Métrica a calcular sobre los valores (LAST_VALUE, MEAN, ST_DEV).
            comparator (my_statistics.Comparator): Comparador que determina cuándo disparar el callback.
            timer_interval (float): Intervalo en segundos entre lecturas de valores.
            read_value (Callable[[], float]): Función que devuelve un valor numérico a añadir a la lista.
            callback: Optional[Callable[[], None]] = None: Función a ejecutar cuando se cumpla la condición.
        """
        self.reference_value = reference_value
        self.metric = metric
        self.comparator = comparator
        self.timer_interval = timer_interval
        self.callback = callback
        self.read_value = read_value  # inyección de dependencia

        self.values = None  # lista de valores con longitud máxima 120
        self.timer = TimeDelay(self.timer_interval, self._timer_task, )
        self.started_time = None
        self.paused_time = None
        self.elapsed_time = 0.0
        self.state = 'initiated'

        # Lock para operaciones thread-safe sobre la lista
        self._values_lock = threading.Lock()

    def start(self):
        """
        Inicia el timer y comienza a leer valores periódicamente.
        :return: None
        """
        if self.state == 'initiated' or self.state == 'paused' or self.state == 'continue':
            if self.state == 'paused':
                self.timer.resume()
            elif self.state == 'initiated':
                self.values = LimitedList(120)  # lista de valores con longitud máxima 120
                self.timer.start()
            elif self.state == 'continue':
                self.timer.reset()
                self.timer.start()
            self.state = 'started'
            self.started_time = time.time()

    def pause(self):
        """
        Pone el timer en modo pause conservando los valores de elapsed time.
        :return: None
        """
        if not self.state == 'started':
            return
        self.timer.pause()
        self.elapsed_time = self.elapsed_time + (time.time() - self.started_time)
        self.state = 'paused'

    def resume(self):
        """
        Reanuda el timer si es que previamente se había ejecutado pause.
        :return: None
        """
        if not self.state == 'paused':
            return
        self.start()

    def reset(self):
        """
        Reinicia el timer a los valores de constructor.
        Ojo. El timer se detiene despues de hacer un reset y se reinician los valores de timeout, remaining y elapsed.
        Remaining time  = timeout, elapsed time = 0s.
        Es necesario volver a hacer un start del timer.
        :return: None
        """
        self.timer.reset()
        self.__init__(self.reference_value,
                      self.metric,
                      self.comparator,
                      self.timer_interval,
                      self.read_value,
                      self.callback
                      )

    def is_done(self) -> bool:
        return self.state == 'done'

    def elapsed(self) -> float:
        """
        Devuelve el tiempo transcurrido desde que se llamó a `start()`.
        :return: float: Tiempo en segundos transcurrido desde `start()`. 0 si no se ha iniciado.
        """
        return self.elapsed_time

    def remaining(self) -> float:
        """
        En este tipo de timer el metodo remaining no tiene sentido.
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
            self.state = 'done'
            self._internal_callback()
        else:
            self.state = 'continue'
            self.start()

    def _internal_callback(self):
        if self.callback:
            self.callback()

    def clear_values(self) -> None:
        """
        Limpia la lista de valores de manera segura (thread-safe).

        Esto puede usarse para reiniciar manualmente la ventana de valores.
        """
        with self._values_lock:
            self.values.clear()

    def __str__(self):
        """
        Devuelve una representación legible del estado actual del StatisticsDelay.
        Incluye los principales parámetros de configuración y el estado de ejecución.
        """
        return (f"StatisticsDelay(v{self.__version__})\n"
                f"  Reference value : {self.reference_value}\n"
                f"  Metric          : {self.metric.name if hasattr(self.metric, 'name') else self.metric}\n"
                f"  Comparator      : {self.comparator.name if hasattr(self.comparator, 'name') else self.comparator}\n"
                f"  Timer interval  : {self.timer_interval}s\n"
                f"  State           : {self.state}\n"
                f"  Elapsed time    : {self.elapsed_time:.3f}s\n"
                f"  Values count    : {len(self.values) if self.values else 0}\n"
                f"  Callback defined: {'Yes' if self.callback else 'No'}")

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
