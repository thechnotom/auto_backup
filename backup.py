from python_utilities import file_counting as fc
from python_utilities import logger as lg
from python_utilities import files as fut
from python_utilities import strings as sut
import json
import sys
import threading
import time
import importlib
import default_operations
import signal


class BackupManager():

    def __init__(self):
        settings = fut.import_json("settings.json")
        if settings is None:
            sys.exit(1)

        self.src = settings["backups"]["src"]
        self.dest_dir = settings["backups"]["dest_dir"]
        self.backup_immediately = settings["backups"]["immediately"]
        self.backup_time = settings["backups"]["time"]
        self.max_num_backups = settings["backups"]["max_num"]
        self.max_use_of_free_space = settings["backups"]["max_use_of_free_space"]
        self.backup_retry_time = settings["backups"]["immediately"]
        self.active = False
        self.timer = None
        self.last_timestamp = float("-inf")

        self.logger = lg.Logger.from_settings_dict(settings["logging"])

        operations_package_name = settings["backups"]["operations_package"]
        try:
            self.operations = importlib.import_module(operations_package_name).Operations
        except Exception as e:
            self.logger.error(f"Could not import operations module \"{operations_package_name}\"")
            self.logger.error(f"Using default no-ops instead")
            self.operations = default_operations.Operations

    def add_message(self, string):
        self.logger.MESSAGE(string)

    @staticmethod
    def start_timer(seconds, callback, args=None, kargs=None):
        timer = threading.Timer(seconds, callback, args, kargs)
        timer.start()
        return timer

    def toggle_state(self, is_user_interaction=True):
        if self.src is None or self.dest_dir is None:
            self.logger.warning("Cannot start timer without a source and a destination")
            return
        if not self.active:
            # Asking to start a timer
            self.logger.interaction("Starting timer")
            if not fut.target_exists(self.src) or not fut.target_exists(self.dest_dir):
                self.logger.error(f"Source \"{self.src}\" and/or destination \"{self.dest_dir}\" does not exist")
                self.add_message("Missing source and/or destination")
                return
            self.timer = BackupManager.start_timer(0 if self.backup_immediately else self.backup_time, self.timer_callback)
        else:
            # Asking to stop a timer
            if is_user_interaction:
                self.logger.interaction("Stopping timer")
            self.timer.cancel()
        self.active = not self.active

    def timer_callback(self):
        self.logger.timer("Timer complete")
        if not fut.target_exists(self.src) or not fut.target_exists(self.dest_dir):
            self.logger.error(f"Source \"{self.src}\" and/or destination \"{self.dest_dir}\" does not exist")
            self.add_message("Missing source and/or destination")
            self.toggle_state(False)
            return
        backup_names = fc.get_backup_names(self.src, self.dest_dir)
        destination = fc.get_relevant_backup_names(self.src, backup_names, self.dest_dir).next
        dest = sut.shorten_string(destination, 15, False, True)

        copy_result = False
        copy_skipped = False
        start_timestamp = None
        copy_duration = None
        end_timestamp = None
        if fut.get_mod_time(self.src) > self.last_timestamp or self.last_timestamp == float("-inf"):
            # Check if an older backup needs to be deleted
            while True:
                backup_names = fc.get_backup_names(self.src, self.dest_dir)
                earliest_backup = fc.get_relevant_backup_names(self.src, backup_names, self.dest_dir).first
                if len(backup_names) < self.max_num_backups:
                    break
                self.logger.operation(f"Deleting \"{earliest_backup}\" as it is the oldest backup")
                if not fut.delete(earliest_backup, self.logger):
                    self.logger.error(f"Could not delete \"{earliest_backup}\"")
                    self.logger.error(f"Cancelling backup since old backups could not be cleared")
                    self.toggle_state(False)
                    return
                self.add_message(f"Deleted \"{sut.shorten_string(earliest_backup, 15, False, True)}\" successfully")

            # Copy the file to a backup
            self.operations.pre_op()
            self.logger.operation(f"Copying \"{self.src}\" to \"{destination}\"")
            self.add_message(f"Starting to copy to \"{dest}\"")
            start_timestamp = fut.get_mod_time(self.src)
            self.last_timestamp = start_timestamp
            start_time = time.time()
            copy_result = fut.copy(self.src, destination, self.max_use_of_free_space, self.logger)
            end_time = time.time()
            copy_duration = round(end_time - start_time, 2)
            end_timestamp = fut.get_mod_time(self.src)
            self.add_message("Copy complete")
            self.operations.post_op()

        else:
            self.add_message("No changes were detected")
            copy_skipped = True

        # Prevent the timer from restarting if the user stops the backup while a file is being copied
        if not self.active:
            self.logger.warning("Prevented timer from restarting (backup was likely stopped during timer callback)")
            return

        # Check if the copy failed
        if (not copy_result) and (not copy_skipped):
            self.logger.operation(f"The copy operation for \"{self.src}\" to \"{self.dest_dir}\" failed")
            self.add_message(f"Copy to \"{dest}\" failed (copy error)")
            self.toggle_state(False)
            return

        # Check if the source file has changed between the start and end of the copy
        # If it has changed, delete the potentially corrupted backup and reset the timer with a quicker timer
        if start_timestamp != end_timestamp and (not copy_skipped):
            self.logger.operation(f"The file \"{self.src}\" changed while being copied")
            self.add_message(f"Copy to \"{dest}\" failed (found changes in source)")
            fut.delete(destination, self.logger)
            self.logger.operation(f"The file \"{destination}\" has been deleted to avoid possible corruption")
            self.logger.timer(f"Restarting timer after failed copy ({self.backup_retry_time} seconds)")
            self.add_message(f"Trying again in {self.backup_retry_time} seconds")
            self.timer = BackupManager.start_timer(self.backup_retry_time, self.timer_callback)
            return

        # If the file was successfully copied or skipped, restart the timer
        if not copy_skipped:
            self.logger.operation(f"The file \"{self.src}\" has been copied to \"{destination}\"")
            self.add_message(f"Copy to \"{dest}\" successful ({copy_duration} seconds)")
        else:
            self.add_message("Copy skipped")
        self.logger.timer(f"Restarting timer after copy ({self.backup_time} seconds)")
        self.timer = BackupManager.start_timer(self.backup_time, self.timer_callback)

# -----------------------
# Driver code
# -----------------------

if __name__ == "__main__":
    backupManager = BackupManager()
    backupManager.logger.info("Program initiated")
    backupManager.toggle_state()  # start backups
    try:
        while True:
            time.sleep(1)  # sleep to prevent high CPU usage
    except KeyboardInterrupt as e:
        backupManager.logger.info("Caught interrupt... stopping backups")
        if backupManager.active:
            backupManager.toggle_state()  # stop backups
        backupManager.logger.info("Waiting for outstanding operations to finish")
        backupManager.timer.join()  # wait for any outstanding timer-related operations
    except Exception as e:
        backupManager.logger.warning("An unknown exception caused the program to halt")
        backupManager.logger.warning(str(e))
        raise e
    backupManager.logger.info("Program terminated")