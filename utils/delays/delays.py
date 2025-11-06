import statistics
import threading
import time
from typing import Callable
from enum import Enum
from abc import ABC, abstractmethod


class DelayState(Enum):
    INITIATED = 'initiated'
    STARTED = 'started'
    PAUSED = 'paused'

class DelayCondition(Enum):
    LAST_ADDED_VALUE_UNDER = "last_added_value_under"
    LAST_ADDED_VALUE_ABOVE = "last_added_value_above"
    MEAN_UNDER = "mean_under"
    MEAN_ABOVE = "mean_above"
    ST_DEV_ABOVE = "st_dev_above"
    ST_DEV_UNDER = "st_dev_under"

class Delay(ABC):
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


# ****************HECHO POR MICROSOFT COPILOT****************************
class TimerDelayCopilot(Delay):
    def __init__(self, timeout: float, callback: Callable[[], None]):
        if timeout <= 0:
            raise ValueError("Timeout debe ser mayor que cero.")
        if not callable(callback):
            raise TypeError("Callback debe ser una función callable.")

        self.timeout = timeout
        self.callback = callback
        self.timer = threading.Timer(timeout, callback)

        self.started_time: float | None = None
        self.paused_time: float | None = None
        self.total_paused_duration: float = 0.0
        self.state = DelayState.INITIATED

    def start(self):
        if self.state != DelayState.STARTED:
            self.started_time = time.time()
            self.timer.start()
            self.state = DelayState.STARTED

    def pause(self):
        if self.state == DelayState.STARTED:
            self.timer.cancel()
            self.paused_time = time.time()
            self.state = DelayState.PAUSED

    def resume(self):
        if self.state == DelayState.PAUSED:
            paused_duration = time.time() - self.paused_time
            self.total_paused_duration += paused_duration
            remaining_time = self.remaining()
            self.timer = threading.Timer(remaining_time, self.callback)
            self.timer.start()
            self.state = DelayState.STARTED

    def reset(self):
        self.timer.cancel()
        self.started_time = None
        self.paused_time = None
        self.total_paused_duration = 0.0
        self.timer = threading.Timer(self.timeout, self.callback)
        self.state = DelayState.INITIATED

    def elapsed(self) -> float:
        if self.state == DelayState.INITIATED or not self.started_time:
            return 0.0
        current_time = self.paused_time if self.state == DelayState.PAUSED else time.time()
        return max(0.0, current_time - self.started_time - self.total_paused_duration)

    def remaining(self) -> float:
        return max(0.0, self.timeout - self.elapsed())


class TimeDelay(Delay):
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


class ThresholdDelay(Delay):

    def __init__(self, threshold: float, mode: str, interval: float, callback: Callable[[], None],
                 read_value: Callable[[], float]):
        self.threshold = threshold
        self.interval = interval
        self.mode = mode
        self.callback = callback
        self.read_value = read_value  # inyección de dependencia
        self.timer = TimeDelay(self.interval, self.check_condition)
        self.started_time = None
        self.state = DelayState.INITIATED
        self.thread = None
        self._stop_event = threading.Event()

    def start(self):
        self.timer.start()

    def pause(self):
        self.timer.pause()

    def resume(self):
        self.timer.resume()

    def reset(self):
        self.timer.reset()

    def elapsed(self) -> float:
        if not self.started_time:
            return 0.0
        return time.time() - self.started_time

    def remaining(self) -> float:
        pass

    def check_condition(self):
        value = self.read_value()
        if self.mode == 'below' and value < self.threshold:
            self.callback()
        elif self.mode == 'above' and value > self.threshold:
            self.callback()
        else:
            self.timer.reset()
            self.timer.start()

class StatisticsDelay(Delay):

    def __init__(self, reference_value: float, condition: DelayCondition, interval: float, callback: Callable[[], None],
                 read_value: Callable[[], float]):
        self.reference_value = reference_value
        self.interval = interval
        self.condition = condition
        self.callback = callback
        self.read_value = read_value  # inyección de dependencia
        self.values = []
        self.timer = TimeDelay(self.interval, self.check_condition)
        self.started_time = None
        self.state = DelayState.INITIATED
        self.thread = None
        self._stop_event = threading.Event()

    def start(self):
        self.timer.start()

    def pause(self):
        self.timer.pause()

    def resume(self):
        self.timer.resume()

    def reset(self):
        self.timer.reset()

    def elapsed(self) -> float:
        if not self.started_time:
            return 0.0
        return time.time() - self.started_time

    def remaining(self) -> float:
        pass

    def timer_task(self):
        self.add_value(self.read_value())
        self.check_condition()

    def add_value(self, value):
        self.values.append(value)

    def check_condition(self):
        if self.statistic == 'below' and value < self.threshold:
            self.callback()
        elif self.statistic == 'above' and value > self.threshold:
            self.callback()
        else:
            self.timer.reset()
            self.timer.start()

    def _compute_metric(self, condition: DelayCondition):
        """Calcula el valor que se usará para comparar con la referencia."""
        if not self.values:
            return None
        if self.condition.name.startswith("LAST_ADDED"):
            return self.values[-1]
        elif self.condition.name.startswith("MEAN"):
            return statistics.mean(self.values)
        elif self.condition.name.startswith("ST_DEV"):
            return statistics.stdev(self.values) if len(self.values) > 1 else 0.0
        else:
            raise ValueError(f"Unknown condition: {self.condition}")