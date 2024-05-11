from abc import abstractmethod, ABC
from time import sleep

from utils.LOG import get_logger, stringify


class WaitingStrategy(ABC):
    @abstractmethod
    def wait(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def decrease(self):
        pass


class FibonacciStrategy(WaitingStrategy):
    def reset(self):
        self.prev = 1
        self.curr = 1
        self.LOG.debug(f"State:  {stringify(self)}")

    def decrease(self):
        if self.curr <= 2:
            self.curr = 1
        else:
            self.prev, self.curr = self.curr - self.prev, self.prev

        self.LOG.debug("State: " + stringify(self))

    def __init__(self):
        self.curr = 1
        self.prev = 1

        self.LOG = get_logger(__name__)
        print("State: " + stringify(self))
        self.LOG.debug(f"State:  {stringify(self)}")

    def __dict__(self):
        return {"prev": self.prev, "curr": self.curr}

    def __str__(self):
        return str(self.__dict__())

    def wait(self):
        sleep(self.curr)
        self.prev, self.curr = self.curr, self.prev + self.curr
        self.LOG.debug(f"State:  {stringify(self)}")
