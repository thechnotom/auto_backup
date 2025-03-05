from abstract_operations import AbstractOperations
from python_utilities.logger import Logger

class Operations(AbstractOperations):

    __log = Logger.make_generic_logger().generic

    @staticmethod
    def pre_op():
        Operations.__log("Default pre-op")

    @staticmethod
    def post_op():
        Operations.__log("Default post-op")