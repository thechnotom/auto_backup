from .backup_manager import BackupManager
from .python_utilities.logger import Logger, LoggerExceptions
import threading
import time


class BackupOverseer:

    def __init__(self, logger=None):
        self.logger = logger
        if logger is None:
            self.logger = Logger(
                types={},
                printer=print,
                identifier="OVERSEER",
                do_timestamp=True,
                do_type=True,
                do_location=True,
                do_short_location=False,
                do_thread_name=True
            )
        
        try:
            self.logger.add_all_types(["info", "warning"])
        except LoggerExceptions.OverrideLoggerTypeException as e:
            pass

        self.managers = {}  # key: manager name; value: dict { manager, thread }


    @staticmethod
    def from_settings_dict(settings, logger=None):
        overseer = BackupOverseer(logger)
        for details in settings["managers"]:
            manager_logger = logger
            if details["logging"] is not None:
                manager_logger = Logger.from_settings_dict_incl_printer(details["logging"])
            else:
                logger_settings = overseer.logger.to_settings_dict()
                logger_settings["logger"]["identifier"] = details["name"]
                manager_logger = Logger.from_settings_dict(logger_settings["logger"], logger_settings["printer_function"])
            overseer.add_manager(BackupManager.from_settings_dict(details["manager"], manager_logger, details["name"]))
        return overseer


    def get_all_manager_names(self):
        return list(self.managers.keys())


    def get_all_managers(self):
        return self.managers


    def get_manager(self, manager_name):
        return self.managers[manager_name]["manager"]


    def get_thread(self, manager_name):
        return self.managers[manager_name]["thread"]


    def add_manager(self, manager):
        if manager.get_name() in self.managers:
            return False
        self.managers[manager.get_name()] = {
            "manager": manager,
            "thread": self.__create_manager_thread(manager.get_name())
        }
        return True


    def remove_manager(self, manager_name, stop_manager=True):
        if manager_name not in self.managers:
            return False
        if stop_manager:
            result = self.stop_manager(manager_name)
            if not result:
                return False
        self.managers.pop(manager_name)
        return True


    def __create_manager_thread(self, manager_name):
        def thread_func():
            manager = self.get_manager(manager_name)
            manager.start_backup()
            while self.is_manager_active(manager_name):
                time.sleep(1)
        return threading.Thread(target=thread_func, name=manager_name)


    def is_manager_active(self, manager_name):
        if manager_name not in self.managers:
            return False
        return self.managers[manager_name]["manager"].is_active()


    def start_manager(self, manager_name):
        if manager_name not in self.managers:
            return False
        if self.get_thread(manager_name).is_alive():
            self.logger.info(f"Thread for \"{manager_name}\" is already alive")
            return False
        self.managers[manager_name]["thread"].start()
        return True


    def stop_manager(self, manager_name, wait_for_threads=True):
        if manager_name not in self.managers:
            return False
        result = self.get_manager(manager_name).stop_backup()
        if wait_for_threads:
            self.get_thread(manager_name).join()
        return result


    def start_all(self):
        for manager_name in self.managers:
            self.logger.info(f"Starting manager: {manager_name}")
            self.start_manager(manager_name)


    def stop_all(self, wait_for_threads=True):
        for manager_name in self.managers:
            self.logger.info(f"Stopping manager: {manager_name}")
            self.stop_manager(manager_name, False)
        if wait_for_threads:
            for manager_name in self.managers:
                self.logger.info(f"Waiting for manager: {manager_name}")
                self.get_thread(manager_name).join()
                self.logger.info(f"Manager stopped: {manager_name}")


    def run_all(self, max_time=None):
        self.start_all()

        if max_time is None:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt as e:
                self.logger.info("Caught interrupt... stopping backups")
                self.stop_all()
            except Exception as e:
                self.logger.warning("An unknown exception caused the program to halt")
                self.logger.warning(str(e))
                raise e

        else:
            timer = threading.Timer(max_time, self.stop_all)
            timer.name = f"{self.logger.get_identifier()}-stop-all-timer"
            timer.start()
            if timer is not None:
                timer.join()

        self.logger.info("Program terminated")