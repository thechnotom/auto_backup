from abstract_operations import AbstractOperations
from python_utilities.logger import Logger
from python_utilities.files import import_json
from default_operations import Operations as default_ops
from constants import ResultCodes as rc
import subprocess
import sys
import time

class Operations(AbstractOperations):

    __log = Logger.make_generic_logger().generic
    __settings = import_json("mc_server_operations_settings.json")
    __screen_name = __settings["screen_name"]

    @staticmethod
    def __run_screen_command(command):
        if "linux" not in sys.platform:
            Operations.__log(f"Cannot execute the following screen command on \"{sys.platform}\": {command}")
            return False
        subprocess.run(["screen", "-S", Operations.__screen_name, "-X", "stuff", f"{command}\n"])
        return True

    @staticmethod
    def set_logger_func(logger_func):
        Operations.__log = logger_func

    @staticmethod
    def setup(details):
        Operations.__log("Starting setup")
        Operations.__log("setup: running save-off")
        Operations.__run_screen_command("save-off")
        Operations.__log("setup: completed save-off")
        time.sleep(Operations.__settings["save_off_delay"])
        Operations.__log("setup: running save-all")
        Operations.__run_screen_command("save-all")
        Operations.__log("setup: completed save-all")
        time.sleep(Operations.__settings["save_all_delay"])

    @staticmethod
    def check_need(details):
        return default_ops.check_need(details)

    @staticmethod
    def conditional_setup(details):
        Operations.__log("Starting conditional_setup")

    @staticmethod
    def conditional_cleanup(details):
        Operations.__log("Starting conditional_cleanup")

    @staticmethod
    def cleanup(details):
        Operations.__log("Starting cleanup")
        Operations.__log("cleanup: running save-on")
        Operations.__run_screen_command("save-on")
        Operations.__log("cleanup: completed save-on")
        time.sleep(Operations.__settings["save_on_delay"])

    @staticmethod
    def final(details):
        Operations.__log("Starting final")
        if details.code == rc.SUCCESS:
            if details.skipped:
                Operations.__run_screen_command("say Backup skipped (no changes found)")
            else:
                Operations.__run_screen_command("say Backup successful")

        elif details.code == rc.COPY_ERROR:
            Operations.__run_screen_command("say There was an error copying the backup (backups have halted)")

        elif details.code == rc.SOURCE_CHANGE:
            Operations.__run_screen_command("say The source changed while being backed up (retrying)")

        elif details.code == rc.CANNOT_DELETE_BAD_BACKUP or details.code == rc.CANNOT_DELETE_OLD_BACKUP:
            Operations.__run_screen_command("say Old/bad backup deletion failed (backups have halted)")

        else:
            Operations.__run_screen_command("say Unknown result")
        
        if details.code != rc.SUCCESS:
            Operations.__log(str(details))