import unittest
import libdevlpr as devlpr
import time

class DevlprTest(unittest.TestCase):
    callback_called = False
    def setUp(self) -> None:
        DevlprTest.callback_called = False

    @staticmethod
    def callback(data):
        DevlprTest.callback_called = True

    def test_addCallback(self):
        devlpr.add_callback('raw', 0, DevlprTest.callback)
        time.sleep(1)
        if

    def test_removeCallback(self):
        pass
    def test_stop(self):
        pass