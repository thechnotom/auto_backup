from ..python_utilities.logger import Logger
from ..python_utilities import remote_files as rfut
from ..python_utilities import files as fut
from ..python_utilities import file_counting as fc
from ..python_utilities.files import import_json
from .abstract_operations import AbstractOperations

class Operations(AbstractOperations):

    __log = Logger.make_generic_logger()
    __settings = import_json(fut.path_to_directory(__file__) + "/remote_destination_operations_settings.json")
    __copy_timeout = __settings["copy_timeout"]
    __get_modification_timestamp_timeout = __settings["get_modification_timestamp_timeout"]
    __remote_manager = rfut.ProcessSSH(
        __settings["user"],
        __settings["host"],
        __settings["default_timeout"],
        __log
    )

    @staticmethod
    def set_logger_func(logger_func):
        Operations.__log = logger_func
        Operations.__remote_manager.set_logger(Operations.__log)

    @staticmethod
    def setup(details):
        Operations.__log("Default remote setup")

    @staticmethod
    def check_need(details):
        return details.init_mod_timestamp > details.last_mod_timestamp

    @staticmethod
    def conditional_setup(details):
        Operations.__log("Default remote conditional_setup")

    @staticmethod
    def copy(source, destination):
        return Operations.__remote_manager.copy_to_remote(source, destination, Operations.__copy_timeout)

    @staticmethod
    def conditional_cleanup(details):
        Operations.__log("Default remote conditional_cleanup")

    @staticmethod
    def cleanup(details):
        Operations.__log("Default remote cleanup")

    @staticmethod
    def final(details):
        Operations.__log("Default remote final")

    @staticmethod
    def src_exists(filename):
        return fut.target_exists(filename)

    @staticmethod
    def dest_exists(filename):
        return Operations.__remote_manager.exists(filename)

    @staticmethod
    def delete_dest(filename):
        return Operations.__remote_manager.delete(filename)

    @staticmethod
    def get_src_mod_time(filename, exclusions=None):
        return fut.last_modified(filename, exclusions)

    @staticmethod
    def get_backup_names(source, dest_dir):
        items = Operations.__remote_manager.ls(dest_dir)
        return fc.get_backup_names(source, items)

    @staticmethod
    def get_relevant_backup_names(source, backup_names, dest_dir):
        return fc.get_relevant_backup_names(source, backup_names, dest_dir)