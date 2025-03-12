from abstract_operations import AbstractOperations
from python_utilities.logger import Logger

class Operations(AbstractOperations):

    __log = Logger.make_generic_logger().generic

    @staticmethod
    def init_op():
        Operations.__log("Default init-op")

    @staticmethod
    def check_need_op(source, destination, curr_source_timestamp, last_source_timestamp):
        return curr_source_timestamp > last_source_timestamp

    @staticmethod
    def pre_op():
        Operations.__log("Default pre-op")

    @staticmethod
    def post_op():
        Operations.__log("Default post-op")

    @staticmethod
    def final_op():
        Operations.__log("Default final-op")