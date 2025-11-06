import threading
import unittest
import time
#from distutils.msvccompiler import read_values

from utils.delays.delays import TimeDelay, ThresholdDelay, StatisticsDelay
from utils.my_statistics.my_statistics import Metrics, Comparator


class TestTimerDelay(unittest.TestCase):
    def setUp(self):
        self.callback_called = False

        def callback():
            self.callback_called = True

        self.timeout = 1.0  # 1 segundo
        self.delay = TimeDelay(self.timeout, callback)

    def test_start_and_callback(self):
        self.delay.start()
        time.sleep(self.timeout + 0.2)
        self.assertTrue(self.callback_called)

    def test_pause_and_resume(self):
        self.delay.start()
        time.sleep(0.5)
        self.delay.pause()
        remaining_after_pause = self.delay.remaining()
        time.sleep(0.5)  # No debería afectar el timer
        self.delay.resume()
        time.sleep(remaining_after_pause + 0.2)
        self.assertTrue(self.callback_called)

    def test_reset(self):
        self.delay.start()
        time.sleep(0.5)
        self.delay.reset()
        self.assertEqual(self.delay.elapsed(), 0.0)
        self.assertEqual(self.delay.remaining(), self.timeout)
        self.assertFalse(self.callback_called)

    def test_elapsed_and_remaining(self):
        self.delay.start()
        time.sleep(0.3)
        elapsed = self.delay.elapsed()
        remaining = self.delay.remaining()
        self.assertAlmostEqual(elapsed + remaining, self.timeout, delta=0.05)

    def test_multiple_pauses(self):
        self.delay.start()
        time.sleep(0.3)
        self.delay.pause()
        time.sleep(0.2)
        self.delay.resume()
        time.sleep(0.3)
        self.delay.pause()
        time.sleep(0.2)
        self.delay.resume()
        time.sleep(self.delay.remaining() + 0.2)
        self.assertTrue(self.callback_called)

# ====== Función fake de lectura de corriente ======
def make_read_value_fake(start, step):
    """
    #TODO acabar modo ascendiente
    Genera una función que simula una lectura de un valor
    ascendente o descendente linealmente.
    Ejemplo: 10.0, 9.0, 8.0, ...
    """
    actual_value = {"value": start}

    def read_value():
        val = actual_value["value"]
        actual_value["value"] += step
        return val

    return read_value


# ====== Test Suite ======
class TestThresholdDelay(unittest.TestCase):

    def test_callback_triggered_below_threshold(self):
        """
        Verifica que el callback se ejecuta cuando el valor leido cae bajo el umbral.
        """
        callback_called = threading.Event()

        def callback():
            callback_called.set()

        read_value_fake = make_read_value_fake(start=5.0, step=-1.0)
        delay = ThresholdDelay(threshold=3.0, mode='below', interval=0.1,
                               callback=callback, read_value=read_value_fake)
        delay.start()

        # Esperamos un poco más que el intervalo
        time.sleep(1)
        self.assertTrue(callback_called.is_set(),
                        "El callback no se ejecutó al caer por debajo del umbral")

    def test_callback_triggered_above_threshold(self):
        """
        Verifica que el callback se ejecuta cuando el valor leido sobrepasa cierto umbral.
        """
        callback_called = threading.Event()

        def callback():
            callback_called.set()

        read_value_fake = make_read_value_fake(start=5.0, step=1.0)
        delay = ThresholdDelay(threshold=10.0, mode='above', interval=0.1,
                               callback=callback, read_value=read_value_fake)
        delay.start()

        # Esperamos un poco más que el intervalo
        time.sleep(1)
        self.assertTrue(callback_called.is_set(),
                        "El callback no se ejecutó al sobrepasar el  umbral")

    def test_callback_not_triggered_if_above_threshold(self):
        """
        Verifica que el callback NO se ejecuta si el valor leido nunca cae bajo el umbral.
        """
        callback_called = threading.Event()

        def callback():
            callback_called.set()

        read_value_fake = make_read_value_fake(start=10.0, step=0.0)  # siempre 10
        delay = ThresholdDelay(threshold=5.0, mode='below', interval=0.1,
                               callback=callback, read_value=read_value_fake)
        delay.start()

        time.sleep(0.5)
        self.assertFalse(callback_called.is_set(),
                         "El callback no debería haberse ejecutado")

    def test_multiple_checks_until_trigger(self):
        """
        Verifica que check_condition se reprograma hasta que se cumple la condición.
        """
        callback_called = threading.Event()

        def callback():
            callback_called.set()

        read_value_fake = make_read_value_fake(start=6.0, step=-1.0)
        delay = ThresholdDelay(threshold=3.0, mode='below', interval=0.1,
                               callback=callback, read_value=read_value_fake)
        delay.start()

        # Esperar suficiente para varias iteraciones
        time.sleep(0.7)
        self.assertTrue(callback_called.is_set(),
                        "El callback debería haberse ejecutado tras varios intervalos")

class TestStatisticsDelay(unittest.TestCase):
    def test_callback_trigger_last_value_under(self):
        # Lista de valores que harán disparar el callback
        values = [12, 11, 9]

        # Evento para sincronizar el hilo
        callback_called = threading.Event()
        last_called_value = []

        def callback():
            last_called_value.append('called')
            callback_called.set()

        # Generador de valores
        it = iter(values)

        def read_value():
            return next(it)

        sd = StatisticsDelay(
            reference_value=10.0,
            metric=Metrics.LAST_VALUE,
            comparator=Comparator.LESS_THAN,
            timer_interval=0.01,  # timer muy corto
            callback=callback,
            read_value=read_value
        )

        sd.start()

        # Esperamos que se dispare el callback
        callback_called.wait(timeout=1.0)  # máximo 1s

        assert len(last_called_value) == 1
        assert len(sd.values) == 0  # lista vacía tras callback

    def test_window_size_limited_list(self):
        # Generamos más de 120 valores
        values = range(150)
        it = iter(values)
        callback_called = threading.Event()

        def callback():
            callback_called.set()

        def read_value():
            return next(it)

        sd = StatisticsDelay(
            reference_value=999,  # no disparará callback
            metric=Metrics.LAST_VALUE,
            comparator=Comparator.GREATER_THAN,
            timer_interval=0.001,
            callback=callback,
            read_value=read_value
        )

        # Ejecutamos manualmente timer_task varias veces
        for _ in range(150):
            sd._timer_task()

        # Solo debe mantener los últimos 120
        assert len(sd.values) == 120
        assert sd.values[0] == 30
        assert sd.values[-1] == 149

    def test_compute_metric_mean_trigger(self):
        values = [5, 15, 20]
        it = iter(values)
        callback_called = threading.Event()
        last_called_value = []

        def callback():
            last_called_value.append('called')
            callback_called.set()

        def read_value():
            return next(it)

        sd = StatisticsDelay(
            reference_value=10.0,
            metric=Metrics.MEAN,
            comparator=Comparator.GREATER_THAN,
            timer_interval=0.01,
            callback=callback,
            read_value=read_value
        )

        # Ejecutamos timer_task manualmente
        for _ in values:
            sd._timer_task()

        assert len(last_called_value) == 1
        assert len(sd.values) == 0


if __name__ == '__main__':
    unittest.main()
