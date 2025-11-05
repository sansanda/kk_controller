import threading
import unittest
import time
#from distutils.msvccompiler import read_values

from utils.delays.delays import TimeDelay, ThresholdDelay
from utils.delays.delays import TimerDelayCopilot


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


class TestTimerDelayCopilot(unittest.TestCase):
    def setUp(self):
        self.callback_called = False

        def callback():
            self.callback_called = True

        self.timeout = 1.0  # 1 segundo
        self.delay = TimerDelayCopilot(self.timeout, callback)

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
        time.sleep(remaining_after_pause + 1)
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
        time.sleep(self.delay.remaining() + 1)
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

if __name__ == '__main__':
    unittest.main()
