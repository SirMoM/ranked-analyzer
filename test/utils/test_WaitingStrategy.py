from unittest import TestCase

from utils.waiting_strategy import FibonacciStrategy, WaitingStrategy


class TestFibonacciStrategy(TestCase):
    def test_decrease(self):
        classToTest: WaitingStrategy = FibonacciStrategy()
        classToTest.wait()
        classToTest.wait()
        classToTest.wait()
        classToTest.decrease()
        classToTest.decrease()
        classToTest.decrease()

        assert str(classToTest) == str(FibonacciStrategy())
