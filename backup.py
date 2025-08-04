# Must be run from outside of the package

from auto_backup_cli.BackupManager import BackupManager
import sys
from auto_backup_cli.python_utilities import files as fut
from auto_backup_cli.python_utilities import logger as lg

settings_filename = "auto_backup_cli/settings.json"
if len(sys.argv) == 2:
    settings_filename = sys.argv[1]
settings = fut.import_json(settings_filename)
logger = lg.Logger.from_settings_dict(settings["logging"])
BackupManager.run(settings["backups"], logger=logger, name="main")