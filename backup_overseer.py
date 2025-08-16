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
            self.logger.add_type("info", True)
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


    def __create_manager_thread(self, manager_name):
        def thread_func():
            manager = self.get_manager(manager_name)
            manager.start_backup()
            while self.is_manager_active(manager_name):
                time.sleep(1)
            result = manager.stop_backup()
            if not result:
                self.logger.info(f"Manager \"{manager_name}\" is already not active")
        return threading.Thread(target=thread_func, name=manager_name)


    def is_manager_active(self, manager_name):
        if manager_name not in self.managers:
            return False
        return self.managers[manager_name]["manager"].is_active()


    def start_manager_thread(self, manager_name):
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
        for key in self.managers:
            self.logger.info(f"Starting manager: {key}")
            self.start_manager_thread(key)


    def stop_all(self, wait_for_threads=True):
        for key in self.managers:
            self.logger.info(f"Stopping manager: {key}")
            self.stop_manager(key, False)
        if wait_for_threads:
            for key, manager_objects in self.managers.items():
                self.logger.info(f"Waiting for manager: {key}")
                self.get_thread(key).join()
                self.logger.info(f"Manager stopped: {key}")