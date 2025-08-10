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
    def copy(source, destination, max_use_of_free_space):
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

    @staticmethod
    @abstractmethod
    def src_exists(filename):
        pass

    @staticmethod
    @abstractmethod
    def dest_exists(filename):
        pass

    @staticmethod
    @abstractmethod
    def delete_dest(filename):
        pass

    @staticmethod
    @abstractmethod
    def get_src_mod_time(filename):
        pass

    @staticmethod
    @abstractmethod
    def get_backup_names(source, dest_dir):
        pass

    @staticmethod
    @abstractmethod
    def get_relevant_backup_names(source, backup_names, dest_dir):
        pass