import threading
import time
from typing import Callable
from enum import Enum
from abc import ABC, abstractmethod


class DelayState(Enum):
    INITIATED = 'initiated'
    STARTED = 'started'
    PAUSED = 'paused'


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


class TimerDelay(Delay):
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

class CurrentDelay(Delay):
    def __init__(self, threshold: float, interval: float, callback: Callable[[], None], read_current: Callable[[], float]):
        self.threshold = threshold
        self.interval = interval
        self.callback = callback
        self.read_current = read_current  # inyección de dependencia
        self.started_time = None
        self.state = DelayState.INITIATED
        self.thread = None
        self._stop_event = threading.Event()

    def _monitor(self):
        while not self._stop_event.is_set():
            current = self.read_current()
            if current < self.threshold:
                self.callback()
                break
            time.sleep(self.interval)

    def start(self):
        if self.state != DelayState.STARTED:
            self.started_time = time.time()
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._monitor)
            self.thread.start()
            self.state = DelayState.STARTED

    def pause(self):
        # No se puede pausar un proceso de muestreo continuo de forma trivial
        pass

    def resume(self):
        # No aplicable si no hay pausa
        pass

    def reset(self):
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.started_time = None
        self.state = DelayState.INITIATED

    def elapsed(self) -> float:
        if not self.started_time:
            return 0.0
        return time.time() - self.started_time



#
# class ThresholdDelay(Delay):
#     """
#     Delay basado en un umbral de valor usando una actualización explícita.
#     """
#
#     def __init__(self, threshold: float, condition: str = 'above', callback: callable = None):
#         if condition not in ['above', 'below']:
#             raise ValueError("La condición debe ser 'above' o 'below'.")
#         self.threshold = threshold
#         self.condition = condition
#         self.callback = callback
#         self.value = None  # Inicia como None, hasta que se asigne un valor válido
#         # self.is_paused = False      # Eliminamos el estado de pausado
#         # self.reset_called = False   # Flag para asegurarnos que no se llame al reset accidentalmente
#
#     def start(self):
#         """
#         En este caso start no tiene sentido.
#         :return: None
#         """
#         # """Inicia el delay sin bloquear el hilo principal. Sin evaluación automática."""
#         # print(f"Delay iniciado. Esperando que el valor esté {self.condition} de {self.threshold}.")
#         # # Automáticamente saltará si self.value = None al iniciar el delay
#         # self.evaluate_condition()
#
#     def pause(self):
#         """
#         En este caso start no tiene sentido.
#         :return: None
#         """
#         pass
#
#     def resume(self):
#         """
#         En este caso start no tiene sentido.
#         :return: None
#         """
#         pass
#
#     def reset(self):
#         """
#         Resetea el estado del delay self.value = None.
#         :return:
#         """
#         self.value = None  # Reseteamos el valor también
#         print("Delay reseteado. Esperando nuevo valor.")
#
#     def _evaluate_condition(self):
#         """
#         Evalúa la condición y ejecuta el callback si se cumple.
#         :return None:
#         """
#         print(f"Evaluando valor: {self.value}")
#         if (self.condition == 'above' and self.value > self.threshold) \
#                 or (self.condition == 'below' and self.value < self.threshold):
#             print("Condición cumplida.")
#             match = True
#         else:
#             match = False
#             print("La condición no se cumple. Esperando la próxima actualización de valor.")
#
#         if self.callback and match:
#             self.callback()
#             self.reset()
#
#     def update_value(self, value: float):
#         """
#         Actualiza el valor a evaluar y llama para realizar la comprobación.
#         :param value: Nuevo valor a evaluar
#         :return: None
#         """
#         self.value = value
#         print(f"Valor actualizado a: {self.value}")
#         self._evaluate_condition()
