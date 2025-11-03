import threading
import time
from utils.delays.base import Delay, TimeDelay


class MyTimeDelay(TimeDelay):
    """
    Delay basado en el tiempo (sin usar sleep).
    """

    def __init__(self, interval, function, args=None, kwargs=None):
        self.interval = interval
        self.function = function
        self.started_at = None

    def elapsed(self):
        return time.time() - self.started_at

    def remaining(self):
        return self.interval - self.elapsed()

    def start(self):
        """Inicia el delay sin bloquear el hilo principal."""
        self.started_at = time.time()
        threading.Timer.start(self)

    def pause(self):
        """Pausa el temporizador sin bloquear el hilo principal."""
        threading.Timer.cancel()
        self.interval = self.remaining()

    def resume(self):
        """Reanuda el temporizador desde donde se dejó."""
        with self.lock:
            if self.is_paused:
                self.is_paused = False
                self._start_timer()
                print("Delay reanudado.")
            else:
                print("El delay no está pausado.")

    def reset(self):
        """Resetea el estado del delay."""
        with self.lock:
            if self.timer:
                self.timer.cancel()
            self.remaining_time = self.interval
            self.is_paused = False
            print("Delay reseteado.")


class ThresholdDelay(Delay):
    """
    Delay basado en un umbral de valor usando una actualización explícita.
    """

    def __init__(self, threshold: float, condition: str = 'above', callback: callable = None):
        if condition not in ['above', 'below']:
            raise ValueError("La condición debe ser 'above' o 'below'.")
        self.threshold = threshold
        self.condition = condition
        self.callback = callback
        self.value = None  # Inicia como None, hasta que se asigne un valor válido
        # self.is_paused = False      # Eliminamos el estado de pausado
        # self.reset_called = False   # Flag para asegurarnos que no se llame al reset accidentalmente

    def start(self):
        """
        En este caso start no tiene sentido.
        :return: None
        """
        # """Inicia el delay sin bloquear el hilo principal. Sin evaluación automática."""
        # print(f"Delay iniciado. Esperando que el valor esté {self.condition} de {self.threshold}.")
        # # Automáticamente saltará si self.value = None al iniciar el delay
        # self.evaluate_condition()

    def pause(self):
        """
        En este caso start no tiene sentido.
        :return: None
        """
        pass

    def resume(self):
        """
        En este caso start no tiene sentido.
        :return: None
        """
        pass

    def reset(self):
        """
        Resetea el estado del delay self.value = None.
        :return:
        """
        self.value = None  # Reseteamos el valor también
        print("Delay reseteado. Esperando nuevo valor.")

    def _evaluate_condition(self):
        """
        Evalúa la condición y ejecuta el callback si se cumple.
        :return None:
        """
        print(f"Evaluando valor: {self.value}")
        if (self.condition == 'above' and self.value > self.threshold) \
                or (self.condition == 'below' and self.value < self.threshold):
            print("Condición cumplida.")
            match = True
        else:
            match = False
            print("La condición no se cumple. Esperando la próxima actualización de valor.")

        if self.callback and match:
            self.callback()
            self.reset()

    def update_value(self, value: float):
        """
        Actualiza el valor a evaluar y llama para realizar la comprobación.
        :param value: Nuevo valor a evaluar
        :return: None
        """
        self.value = value
        print(f"Valor actualizado a: {self.value}")
        self._evaluate_condition()
