from .python_utilities.logger import Logger
from .python_utilities import remote_files as rfut
from .python_utilities import files as fut
from .python_utilities import file_counting as fc
from .abstract_operations import AbstractOperations

class Operations(AbstractOperations):

    __log = Logger.make_generic_logger()
    #__remote_manager = rfut.ProcessSSH("thoma", "raspberrypi", 3, __log)  # TODO: set programmatically
    __remote_manager = rfut.ProcessSSH("deck", "192.168.2.35", 10, __log)  # TODO: set programmatically

    @staticmethod
    def set_logger_func(logger_func):
        Operations.__log = logger_func

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
    def copy(source, destination, max_use_of_free_space):
        return Operations.__remote_manager.copy_to_remote(source, destination)

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
    def get_src_mod_time(filename):
        return fut.get_mod_time(filename)

    @staticmethod
    def get_backup_names(source, dest_dir):
        items = Operations.__remote_manager.ls(dest_dir)
        return fc.get_backup_names(source, items)

    @staticmethod
    def get_relevant_backup_names(source, backup_names, dest_dir):
        return fc.get_relevant_backup_names(source, backup_names, dest_dir)