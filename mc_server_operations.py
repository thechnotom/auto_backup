from abstract_operations import AbstractOperations
from python_utilities.logger import Logger
from python_utilities.files import import_json
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
    def pre_op():
        Operations.__log("Starting pre-op")
        Operations.__log("pre-op: running save-off")
        Operations.__run_screen_command("save-off")
        Operations.__log("pre-op: completed save-off")
        time.sleep(Operations.__settings["save_off_delay"])
        Operations.__log("pre-op: running save-all")
        Operations.__run_screen_command("save-all")
        Operations.__log("pre-op: completed save-all")
        time.sleep(Operations.__settings["save_all_delay"])

    @staticmethod
    def post_op():
        Operations.__log("Starting post-op")
        Operations.__log("post-op: running save-on")
        Operations.__run_screen_command("save-on")
        Operations.__log("post-op: completed save-on")
        time.sleep(Operations.__settings["save_on_delay"])
