from abc import ABC, abstractmethod

class AbstractOperations(ABC):

    @staticmethod
    @abstractmethod
    def pre_op():
        pass

    @staticmethod
    @abstractmethod
    def post_op():
        pass