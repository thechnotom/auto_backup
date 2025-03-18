from abc import ABC, abstractmethod

class AbstractOperations(ABC):

    __log = print

    @staticmethod
    @abstractmethod
    def set_logger_func(logger_func):
        pass

    @staticmethod
    @abstractmethod
    def setup(details):
        pass

    @staticmethod
    @abstractmethod
    def check_need(details):
        pass

    @staticmethod
    @abstractmethod
    def conditional_setup(details):
        pass

    @staticmethod
    @abstractmethod
    def conditional_cleanup(details):
        pass

    @staticmethod
    @abstractmethod
    def cleanup(details):
        pass

    @staticmethod
    @abstractmethod
    def final(details):
        pass