from .python_utilities import logger as lg
from .python_utilities import strings as sut
from .CopyDetails import CopyDetails
from .constants import ResultCodes as rc
from .constants import StatusCodes as sc
from .constants import ExitCodes as ec
from .operations.local_operations import Operations as default_operations
import sys
import threading
import time
import importlib.util


class BackupManager():

    def __init__(
        self,
        src,
        dest_dir,
        name=None,
        max_num_backups=5,
        backup_time=300,
        backup_retry_time=30,
        backup_immediately=True,
        operations_module_name=None,
        operations_module_filename=None,
        allow_skip=False,
        skip_check_exclusions=None,
        permit_copy_failure=False,
        permit_bad_backup_delete_failure=False,
        permit_old_backup_delete_failure=False,
        logger=None
    ):
        self.name = name
        self.src = src
        self.dest_dir = dest_dir
        self.backup_immediately = backup_immediately
        self.backup_time = backup_time
        self.max_num_backups = max_num_backups
        self.backup_retry_time = backup_retry_time
        self.active = False
        self.timer = None
        self.last_timestamp = float("-inf")
        self.allow_skip = allow_skip
        self.skip_check_exclusions = skip_check_exclusions
        self.permit_copy_failure = permit_copy_failure
        self.permit_bad_backup_delete_failure = permit_bad_backup_delete_failure
        self.permit_old_backup_delete_failure = permit_old_backup_delete_failure

        self.status = sc.INACTIVE
        self.exit_code = None

        # Make sure the logger (whether given or created here) has the expected logger types
        self.__required_logger_types = ["info", "warning", "error", "timer", "operation", "interaction", "backup", "MESSAGE"]
        self.logger = logger
        if self.logger is None:
            self.logger = lg.Logger(
                types=None,
                printer=lg.Logger.default_print,
                do_timestamp=True,
                do_type=True,
                do_location=True,
                do_short_location=False,
                do_thread_name=True,
                do_type_missing_indicator=True,
                do_strict_types=False
            )
        self.logger.add_all_types(self.__required_logger_types)

        try:
            spec = importlib.util.spec_from_file_location(operations_module_name, operations_module_filename)
            operations_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(operations_module)
            self.operations = operations_module.Operations
            self.logger.info(f"Loaded operatons package \"{operations_module_name}\" from: {operations_module_filename}")
        except Exception as e:
            self.logger.warning(f"Could not import operations module \"{operations_module_name}\" from: {operations_module_filename}")
            self.logger.warning(f"Caught: {e}")
            self.logger.warning(f"Using default local operations instead")
            self.operations = default_operations
        self.operations.set_logger_func(self.logger.operation)


    @staticmethod
    def from_settings_dict(settings, logger=None, name=None):
        return BackupManager(
            src=settings["src"],
            dest_dir=settings["dest_dir"],
            name=name,
            max_num_backups=settings["max_num"],
            backup_time=settings["time"],
            backup_retry_time=settings["retry_time"],
            backup_immediately=settings["immediately"],
            operations_module_name=settings["operations_module_name"],
            operations_module_filename=settings["operations_module_filename"],
            allow_skip=settings["allow_skip"],
            skip_check_exclusions=settings["skip_check_exclusions"],
            permit_copy_failure=settings["permit_copy_failure"],
            permit_bad_backup_delete_failure=settings["permit_bad_backup_delete_failure"],
            permit_old_backup_delete_failure=settings["permit_old_backup_delete_failure"],
            logger=logger
        )


    def get_required_logger_types():
        return self.__required_logger_types.copy()


    def is_active(self):
        return self.active


    def get_status(self):
        return self.status


    def get_exit_code(self):
        return self.exit_code


    def get_name(self):
        return self.name


    def add_message(self, string):
        self.logger.MESSAGE(string)


    def source_exists(self):
        return self.operations.src_exists(self.src)


    def dest_exists(self):
        return self.operations.dest_exists(self.dest_dir)


    def get_source_mod_time(self):
        return self.operations.get_src_mod_time(self.src, self.skip_check_exclusions)

    def start_timer(self, seconds, callback, args=None, kargs=None):
        timer = threading.Timer(seconds, callback, args, kargs)
        timer.name = f"{self.name if self.name is not None else 'manager'}-timer"
        timer.start()
        return timer


    def __start_retry_timer(self):
        self.logger.timer(f"Trying again in {self.backup_retry_time} seconds")
        self.add_message(f"Trying again in {self.backup_retry_time} seconds")
        self.status = sc.WAITING_FOR_RETRY
        self.timer = self.start_timer(self.backup_retry_time, self.timer_callback)


    def toggle_state(self, is_user_interaction=True):
        if self.src is None or self.dest_dir is None:
            self.logger.warning("Cannot start timer without a source and a destination")
            return
        if not self.active:
            # Asking to start a timer
            self.logger.interaction("Starting timer")
            if not self.source_exists() or not self.dest_exists():
                self.logger.error(f"Source \"{self.src}\" and/or destination \"{self.dest_dir}\" does not exist")
                self.add_message("Missing source and/or destination")
                self.status = sc.ERROR
                self.exit_code =  ec.MISSING_SOURCE_OR_DESTINATION
                return
            self.status = sc.WAITING_FOR_TIMER
            self.timer = self.start_timer(0 if self.backup_immediately else self.backup_time, self.timer_callback)
        else:
            # Asking to stop a timer
            if is_user_interaction:
                self.logger.interaction("Stopping timer")
            self.status = sc.INACTIVE
            self.timer.cancel()
        self.active = not self.active


    def timer_callback(self):
        self.logger.timer("Timer complete")
        if not self.source_exists() or not self.dest_exists():
            self.logger.error(f"Source \"{self.src}\" and/or destination \"{self.dest_dir}\" does not exist")
            self.add_message("Missing source and/or destination")
            self.__start_retry_timer()
            self.exit_code =  ec.CONTROLLED
            return
        backup_names = self.operations.get_backup_names(self.src, self.dest_dir)
        destination = self.operations.get_relevant_backup_names(self.src, backup_names, self.dest_dir).next
        dest = sut.shorten_string(destination, 15, False, True)

        copy_details = CopyDetails()
        copy_details.src = self.src
        copy_details.dest = destination
        copy_details.last_mod_timestamp = self.last_timestamp
        copy_details.init_mod_timestamp = self.get_source_mod_time()

        self.operations.setup(copy_details)

        copy_result = False
        copy_skipped = False
        start_timestamp = None
        copy_duration = None
        end_timestamp = None
        if (not self.allow_skip) or self.operations.check_need(copy_details):
            # Copy the file to a backup
            self.operations.conditional_setup(copy_details)
            self.logger.backup(f"Copying \"{self.src}\" to \"{destination}\"")
            self.add_message(f"Starting to copy to \"{dest}\"")
            self.status = sc.COPYING
            start_timestamp = self.get_source_mod_time()
            self.last_timestamp = start_timestamp
            start_time = time.time()
            copy_result = self.operations.copy(self.src, destination)
            end_time = time.time()
            copy_duration = round(end_time - start_time, 2)
            end_timestamp = self.get_source_mod_time()
            self.logger.backup("Copy complete")
            self.add_message("Copy complete")
            self.status = sc.COPY_COMPLETE

            copy_details.start_time = start_time
            copy_details.end_time = end_time
            copy_details.start_timestamp = start_timestamp
            copy_details.end_timestamp = end_timestamp
            copy_details.last_mod_timestamp = self.last_timestamp
            copy_details.copy_result = copy_result
            self.operations.conditional_cleanup(copy_details)

        else:
            self.add_message("No changes were detected")
            copy_skipped = True

        copy_details.skipped = copy_skipped
        self.operations.cleanup(copy_details)

        # Prevent the timer from restarting if the user stops the backup while a file is being copied
        if not self.active:
            self.logger.warning("Prevented timer from restarting (backup was likely stopped during timer callback)")
            return

        # Check if the copy failed
        if (not copy_result) and (not copy_skipped):
            self.logger.backup(f"The copy operation for \"{self.src}\" to \"{self.dest_dir}\" failed")
            self.add_message(f"Copy to \"{dest}\" failed (copy error)")
            copy_details.result = False
            copy_details.code = rc.COPY_ERROR
            self.operations.final(copy_details)
            if not self.permit_copy_failure:
                self.toggle_state(False)
                self.exit_code = ec.COPY_FAILURE
                return
            self.logger.timer(f"Restarting timer after copy operation failed")
            self.add_message(f"Retrying in {self.backup_retry_time}s")
            self.__start_retry_timer()
            self.exit_code = ec.CONTROLLED
            return

        # Check if the source file has changed between the start and end of the copy
        # If it has changed, delete the potentially corrupted backup and reset the timer with a quicker timer
        if start_timestamp != end_timestamp and (not copy_skipped):
            self.logger.warning(f"The file \"{self.src}\" changed while being copied")
            self.add_message(f"Copy to \"{dest}\" failed (found changes in source)")
            self.logger.backup(f"Attempting to delete the file \"{destination}\" to avoid possible corruption")
            if not self.operations.delete_dest(destination):
                self.logger.error(f"Could not delete \"{destination}\"")
                copy_details.result = False
                copy_details.code = rc.CANNOT_DELETE_BAD_BACKUP
                self.operations.final(copy_details)
                if not self.permit_bad_backup_delete_failure:
                    self.logger.error(f"Cancelling backup since bad backup could not be deleted")
                    self.toggle_state(False)
                    self.exit_code = ec.DELETE_BAD_BACKUP_FAILURE
                    return
            else:
                self.logger.backup(f"Successfully deleted \"{destination}\"")
            copy_details.result = False
            copy_details.code = rc.SOURCE_CHANGE
            self.operations.final(copy_details)
            self.logger.timer(f"Restarting timer after failed copy ({copy_duration} seconds)")
            self.__start_retry_timer()
            self.exit_code = ec.CONTROLLED
            return

        # If the file was successfully copied or skipped, restart the timer
        if not copy_skipped:
            self.logger.backup(f"The file \"{self.src}\" has been copied to \"{destination}\" ({copy_duration} seconds)")
            self.add_message(f"Copy to \"{dest}\" successful ({copy_duration} seconds)")

            # Check if an older backup needs to be deleted
            while True:
                self.status = sc.DELETING_OLD_BACKUPS
                backup_names = self.operations.get_backup_names(self.src, self.dest_dir)
                if len(backup_names) <= self.max_num_backups:
                    break
                earliest_backup = self.operations.get_relevant_backup_names(self.src, backup_names, self.dest_dir).first
                self.logger.backup(f"Deleting \"{earliest_backup}\" as it is the oldest backup")
                if not self.operations.delete_dest(earliest_backup):
                    self.logger.error(f"Could not delete \"{earliest_backup}\"")
                    copy_details.result = False
                    copy_details.code = rc.CANNOT_DELETE_OLD_BACKUP
                    if not self.permit_old_backup_delete_failure:
                        self.logger.error(f"Cancelling backup since old backups could not be cleared")
                        self.toggle_state(False)
                        self.operations.final(copy_details)
                        self.exit_code = ec.DELETE_OLD_BACKUP_FAILURE
                        return
                    break
                else:
                    self.logger.info(f"Deleted \"{earliest_backup}\" successfully")
                    self.add_message(f"Deleted \"{sut.shorten_string(earliest_backup, 15, False, True)}\" successfully")

        else:
            self.logger.info("Copy skipped")
            self.add_message("Copy skipped")

        copy_details.result = True
        copy_details.code = rc.SUCCESS
        self.operations.final(copy_details)
        self.logger.timer(f"Restarting timer after copy ({self.backup_time} seconds)")
        self.status = sc.WAITING_FOR_TIMER
        self.timer = self.start_timer(self.backup_time, self.timer_callback)


    def start_backup(self):
        self.logger.info(f"Initiating backups via \"{self.name}\"")
        if self.active:
            return False
        self.toggle_state(True)  # start backups
        return True


    def stop_backup(self):
        self.logger.info(f"Stopping backups for \"{self.name}\"")
        if not self.active:
            return False
        self.toggle_state(False)  # stop backups

        self.logger.info("Waiting for outstanding operations to finish")
        if self.timer is not None:
            self.timer.join()  # wait for any outstanding timer-related operations

        self.logger.info("Backups terminated")
        return True


    @staticmethod
    def run(settings, logger=None, name=None):
        backupManager = BackupManager(settings, logger, name)
        backupManager.start_backup()
        try:
            while backupManager.is_active():
                time.sleep(1)  # sleep to prevent high CPU usage
        except KeyboardInterrupt as e:
            backupManager.logger.info("Caught interrupt... stopping backups")
            backupManager.stop_backup()
        except Exception as e:
            backupManager.logger.warning("An unknown exception caused the program to halt")
            backupManager.logger.warning(str(e))
            raise e
        backupManager.logger.info("Program terminated")