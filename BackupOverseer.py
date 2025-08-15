from BackupManager import BackupManager
from python_utilities.logger import Logger
import threading
import time


class BackupOverseer:

    def __init__(self, logger=None):
        self.logger = logger
        if logger is None:
            self.logger = Logger(
                types={"info": True},
                printer=print,
                identifier="OVERSEER"
            )

        self.logger.add_all_types("info")

        self.managers = {}


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
                manager_logger = Logger.from_settings_dict(logger_settings["logger"], logger_settings["printer"])
            overseer.add_manager(BackupManager.from_settings_dict(details["manager"], manager_logger, details["name"]))
        return overseer


    def get_all_manager_names(self):
        return list(self.managers.keys())


    def get_all_managers():
        result = []
        for manager in self.managers:
            result.append(manager)
        return result


    def add_manager(self, manager):
        if manager.get_name() in self.managers:
            return False
        self.managers[manager.get_name()] = {
            "manager": manager,
            "thread": self.__create_manager_thread(manager)
        }
        return True


    def __create_manager_thread(self, manager_name):
        def thread_func():
            self.start_manager(manager_name)
            while self.is_manager_active(manager_name):
                time.sleep(1)
            result = self.stop_manager(manager_name)
            if not result:
                logger.info(f"Manager \"{manager_name}\" is already not active")
        return threading.Thread(target=thread_func, name=manager.get_name())


    def is_manager_active(self, manager_name):
        if manager_name not in self.managers:
            return False
        return self.managers[manager_name]["manager"].is_active()


    def start_manager(self, manager_name):
        if manager_name not in self.managers:
            return False
        self.managers[manager_name]["thread"].start()
        return True


    def stop_manager(self, manager_name):
        if manager_name not in self.managers:
            return False
        return self.managers[manager_name]["manager"].stop_backup()


    def start_all(self):
        for key in self.managers:
            self.logger.info(f"Starting manager: {key}")
            self.start_manager(key)


    def stop_all(self):
        for key in self.managers:
            self.logger.info(f"Stopping manager: {key}")
            self.stop_manager(key)