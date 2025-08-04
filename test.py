# Must be run from outside of the package

#from . import backup
from BackupManager import BackupManager
from python_utilities import files as fut

settings = fut.import_json("settings.json")["backups"]

BackupManager.run(settings, None, None)

#bg_manager = backup.BackupManager(settings, None, None)
#bg_manager.start_backup()