from abc import ABC, abstractmethod

class BaseMessage(ABC):
    @classmethod
    @abstractmethod
    def from_data(cls, data):
        pass

    @abstractmethod
    def get_value(self):
        pass