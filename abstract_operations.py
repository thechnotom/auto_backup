from abc import ABC, abstractmethod

class AbstractOperations(ABC):

    @staticmethod
    @abstractmethod
    def init_op():
        pass

    @staticmethod
    @abstractmethod
    def check_need_op(source, destination, curr_source_timestamp, last_source_timestamp):
        pass

    @staticmethod
    @abstractmethod
    def pre_op():
        pass

    @staticmethod
    @abstractmethod
    def post_op():
        pass

    @staticmethod
    @abstractmethod
    def final_op():
        pass