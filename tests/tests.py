import threading
import unittest
import time

from utils.delays.delays import DelayFactory, DelayType, TimeDelay, DelayState  # 👈 usamos la factoría
from utils.my_statistics.my_statistics import Metrics, Comparator


# ====== Test Suite ======

class TestTimeDelay(unittest.TestCase):
    def setUp(self):
        self.callback_called = False

    def callback(self):
        self.callback_called = True

    def test_initial_state(self):
        td = TimeDelay(timeout=1, callback=self.callback)
        self.assertEqual(td.state, DelayState.INITIATED)
        self.assertFalse(td.is_done())
        self.assertAlmostEqual(td.remaining(), 1, delta=0.01)
        self.assertAlmostEqual(td.elapsed(), 0, delta=0.01)

    def test_start_and_done(self):
        td = TimeDelay(timeout=0.2, callback=self.callback)
        td.start()
        self.assertEqual(td.state, DelayState.STARTED)
        time.sleep(0.3)  # Espera que termine
        self.assertTrue(td.is_done())
        self.assertTrue(self.callback_called)

    def test_start_and_done_with_callback_none(self):
        td = TimeDelay(timeout=0.2, callback=None)
        td.start()
        self.assertEqual(td.state, DelayState.STARTED)
        time.sleep(0.3)  # Espera que termine
        self.assertTrue(td.is_done())

    def test_pause_and_resume(self):
        td = TimeDelay(timeout=0.5, callback=self.callback)
        td.start()
        time.sleep(0.2)
        td.pause()
        paused_remaining = td.remaining()
        self.assertEqual(td.state, DelayState.PAUSED)
        time.sleep(0.2)  # No debería afectar al tiempo restante
        self.assertAlmostEqual(td.remaining(), paused_remaining, delta=0.01)
        td.resume()
        self.assertEqual(td.state, DelayState.STARTED)
        time.sleep(paused_remaining + 0.1)
        self.assertTrue(td.is_done())
        self.assertTrue(self.callback_called)

    def test_reset(self):
        n_shots = 2
        timeout = 0.2
        td = TimeDelay(timeout=0.2, callback=self.callback, n_shots=n_shots)
        td.start()
        td.reset()
        self.assertEqual(td.state, DelayState.INITIATED)
        self.assertFalse(td.is_done())
        self.assertAlmostEqual(td.remaining(), n_shots*timeout, delta=0.01)
        self.assertEqual(td.n_shots, n_shots)

    def test_elapsed_and_remaining_consistency(self):
        td = TimeDelay(timeout=0.3, callback=self.callback)
        td.start()
        time.sleep(0.1)
        elapsed = td.elapsed()
        remaining = td.remaining()
        self.assertAlmostEqual(elapsed + remaining, 0.3, delta=0.02)

    def test_str_output(self):
        td = TimeDelay(timeout=1, callback=self.callback)
        s = str(td)
        print(s)
        self.assertIn("TimeDelay(timeout=1.00s", s)
        self.assertIn("state='initiated'", s)
        self.assertIn("callback=callback", s)


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

        sd.start()
        # hay que dar tiempo para que acabe el delay
        time.sleep(3)
        print(sd.values)
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
            comparator=Comparator.LESS_THAN,
            timer_interval=0.01,
            callback=callback,
            read_value=read_value
        )

        sd.start()
        # Hay que dar tiempo para que acabe el delay
        time.sleep(1)
        assert len(last_called_value) == 1

        # para esta prueba es importante que el primer valor del test no sea menor que el valor medio.
        # esto es así porque el delay comienza a comparar desde el primer valor de values
        # esto habría que solucionarlo

        values = [30, 15, 20]
        it = iter(values)
        callback_called = threading.Event()
        last_called_value = []

        sd = DelayFactory.create_delay(
            delay_type=DelayType.STATISTICS,
            reference_value=10.0,
            metric=Metrics.MEAN,
            comparator=Comparator.LESS_THAN,
            timer_interval=0.01,
            callback=callback,
            read_value=read_value
        )

        sd.start()
        # Hay que dar tiempo para que acabe el delay
        time.sleep(1)
        assert len(last_called_value) == 0


if __name__ == '__main__':
    unittest.main()