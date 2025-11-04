import unittest
import time
from utils.delays.delays import TimerDelay  # Asegúrate de que el archivo se llame timer_delay.py


class TestTimerDelay(unittest.TestCase):
    def setUp(self):
        self.callback_called = False

        def callback():
            self.callback_called = True

        self.timeout = 1.0  # 1 segundo
        self.delay = TimerDelay(self.timeout, callback)

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


if __name__ == '__main__':
    unittest.main()
