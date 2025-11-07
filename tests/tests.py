import threading
import unittest
import time

from utils.delays.delays import DelayFactory, DelayType  # 👈 usamos la factoría
from utils.my_statistics.my_statistics import Metrics, Comparator


# ====== Test Suite ======

class TestTimerDelay(unittest.TestCase):
    def setUp(self):
        self.callback_called = False

        def callback():
            self.callback_called = True

        self.timeout = 1.0  # 1 segundo

        # 👇 Creamos el delay usando la factoría
        self.delay = DelayFactory.create_delay(
            delay_type=DelayType.TIME,
            timeout=self.timeout,
            callback=callback
        )

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
    Genera una función que simula una lectura ascendente o descendente lineal.
    Ejemplo: 10.0, 9.0, 8.0, ...
    """
    actual_value = {"value": start}

    def read_value():
        val = actual_value["value"]
        actual_value["value"] += step
        return val

    return read_value


class TestStatisticsDelay(unittest.TestCase):
    def test_callback_trigger_last_value_under(self):
        values = [12, 11, 9]
        callback_called = threading.Event()
        last_called_value = []

        def callback():
            last_called_value.append('called')
            callback_called.set()

        it = iter(values)

        def read_value():
            return next(it)

        # 👇 Se crea usando la factoría
        sd = DelayFactory.create_delay(
            delay_type=DelayType.STATISTICS,
            reference_value=10.0,
            metric=Metrics.LAST_VALUE,
            comparator=Comparator.LESS_THAN,
            timer_interval=0.01,
            callback=callback,
            read_value=read_value
        )

        sd.start()
        callback_called.wait(timeout=1.0)

        assert len(last_called_value) == 1
        assert len(sd.values) == 0

    def test_window_size_limited_list(self):
        values = range(150)
        it = iter(values)
        callback_called = threading.Event()

        def callback():
            callback_called.set()

        def read_value():
            return next(it)

        sd = DelayFactory.create_delay(
            delay_type=DelayType.STATISTICS,
            reference_value=999,
            metric=Metrics.LAST_VALUE,
            comparator=Comparator.GREATER_THAN,
            timer_interval=0.001,
            callback=callback,
            read_value=read_value
        )

        for _ in range(150):
            sd._timer_task()

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

        sd = DelayFactory.create_delay(
            delay_type=DelayType.STATISTICS,
            reference_value=10.0,
            metric=Metrics.MEAN,
            comparator=Comparator.GREATER_THAN,
            timer_interval=0.01,
            callback=callback,
            read_value=read_value
        )

        for _ in values:
            sd._timer_task()

        assert len(last_called_value) == 1
        assert len(sd.values) == 0


if __name__ == '__main__':
    unittest.main()