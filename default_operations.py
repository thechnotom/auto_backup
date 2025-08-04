from .python_utilities.logger import Logger

class Operations:

    __log = Logger.make_generic_logger()

    @staticmethod
    def set_logger_func(logger_func):
        Operations.__log = logger_func

    @staticmethod
    def setup(details):
        Operations.__log("Default setup")

    @staticmethod
    def check_need(details):
        return details.init_mod_timestamp > details.last_mod_timestamp

    @staticmethod
    def conditional_setup(details):
        Operations.__log("Default conditional_setup")

    @staticmethod
    def conditional_cleanup(details):
        Operations.__log("Default conditional_cleanup")

    @staticmethod
    def cleanup(details):
        Operations.__log("Default cleanup")

    @staticmethod
    def final(details):
        Operations.__log("Default final")