import threading
import time
from utils.delays.base import Delay


class TimerDelay(Delay):
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self.timer = threading.Timer(timeout, callback)
        self.startedTime = None # solo para iniciar
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
