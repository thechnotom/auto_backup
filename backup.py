from python_utilities import file_counting as fc
from python_utilities import logger as lg
from python_utilities import printers
from python_utilities import files as fut
from python_utilities import strings as sut
import json
import sys
import threading
import time


class BackupManager():

    def __init__(self):
        settings = BackupManager.import_settings("settings.json")
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

        printer = printers.select_printer(
            settings["logging"]["do_logging"],
            settings["logging"]["console"]["enable"],
            settings["logging"]["file"]["enable"],
            settings["logging"]["file"]["clear"],
            settings["logging"]["file"]["output_filename"],
            settings["logging"]["file"]["max_file_size"]
        )

        self.logger = lg.Logger(
            settings["logging"]["types"],
            printer=printer,
            do_timestamp=settings["logging"]["do_timestamp"],
            do_type=settings["logging"]["do_type"],
            do_location=settings["logging"]["do_location"],
            do_short_location=settings["logging"]["do_short_location"]
        )

    @staticmethod
    def import_settings(filename):
        lines = None
        try:
            with open(filename, "r") as f:
                lines = f.readlines()
        except FileNotFoundError as e:
            Logger.log(f"Unable to locate and open the file \"{filename}\"")
            return None
        
        return json.loads("".join(lines))

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
        self.logger.operation(f"Copying \"{self.src}\" to \"{destination}\"")
        self.add_message(f"Starting to copy to \"{dest}\"")
        start_timestamp = fut.get_timestamp(self.src)
        start_time = time.time()
        copy_result = fut.copy(self.src, destination, self.max_use_of_free_space, self.logger)
        end_time = time.time()
        copy_duration = round(end_time - start_time, 2)
        end_timestamp = fut.get_timestamp(self.src)

        # Prevent the timer from restarting if the user stops the backup while a file is being copied
        if not self.active:
            self.logger.warning("Prevented timer from restarting (backup was likely stopped during timer callback)")
            return

        # Check if the copy failed
        if not copy_result:
            self.logger.operation(f"The copy operation for \"{self.src}\" to \"{self.dest_dir}\" failed")
            self.add_message(f"Copy to \"{dest}\" failed (copy error)")
            self.toggle_state(False)
            return

        # Check if the source file has changed between the start and end of the copy
        # If it has changed, delete the potentially corrupted backup and reset the timer with a quicker timer
        if start_timestamp != end_timestamp:
            self.logger.operation(f"The file \"{self.src}\" changed while being copied")
            self.add_message(f"Copy to \"{dest}\" failed (found changes in source)")
            fut.delete(destination, self.logger)
            self.logger.operation(f"The file \"{destination}\" has been deleted to avoid possible corruption")
            self.logger.timer(f"Restarting timer after failed copy ({self.backup_retry_time} seconds)")
            self.add_message(f"Trying again in {self.backup_retry_time} seconds")
            self.timer = BackupManager.start_timer(self.backup_retry_time, self.timer_callback)
            return

        # If the file was successfully copied, restart the timer
        self.logger.operation(f"The file \"{self.src}\" has been copied to \"{destination}\"")
        self.add_message(f"Copy to \"{dest}\" successful ({copy_duration} seconds)")
        self.logger.timer(f"Restarting timer after copy ({self.backup_time} seconds)")
        self.timer = BackupManager.start_timer(self.backup_time, self.timer_callback)

# -----------------------
# Driver code
# -----------------------

if __name__ == "__main__":
    backupManager = BackupManager()
    backupManager.logger.MESSAGE("Program initiated")
    backupManager.toggle_state()  # start backups
    try:
        while True:
            pass
    except KeyboardInterrupt as e:
        backupManager.logger.MESSAGE("Caught interrupt... stopping backups")
        backupManager.toggle_state()  # stop backups
    except Exception as e:
        backupManager.logger.MESSAGE("An unknown exception caused the program to halt")
        backupManager.logger.MESSAGE(str(e))
        raise e
    backupManager.logger.MESSAGE("Program terminated")