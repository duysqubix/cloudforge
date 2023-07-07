from pathlib import Path
from datetime import datetime
from enum import Enum
import logging
import sys
import tempfile
import os

__packagename__ = "cloudforge"
__version__ = "0.8.1-dev"

VALID_ENVS = ["dev", "stg", "uat", "prod"]

class ValidEnvs(str, Enum):
    dev  = "dev"
    stg  = "stg"
    uat  = "uat"
    prod = "prod"

TMP_DIR = Path(tempfile.gettempdir())
TFPY_DIR_BASE_NAME = ".terraform-py"
TMP_PATH = TMP_DIR / TFPY_DIR_BASE_NAME

SYNAPSE_ANALYTICS_DB_SETUP_SCRIPT_NAME = "dbo_initial_setup"
DEFAULT_MIGRATION_CONTROL_TABLE_NAME = "MigrationControl"
MSSQL_MIGRATION_CONTROL_TABLE_NAME = f"[dbo].[{DEFAULT_MIGRATION_CONTROL_TABLE_NAME}]"
DEFAULT_ODBC_MSSQL_DRIVER = "ODBC Driver 17 for SQL Server"


class UnsupportedDevEnvironment(Exception):
    pass


class ColoredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_ = f"%(asctime)s|%(name)s|%(levelname)s|{'.'*20:>20}%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_ + reset,
        logging.INFO: grey + format_ + reset,
        logging.WARNING: yellow + format_ + reset,
        logging.ERROR: red + format_ + reset,
        logging.CRITICAL: bold_red + format_ + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class ECLogger:
    def __init__(self, level=logging.WARNING, format=ColoredFormatter()):
        self._format_str = format
        self._level = level
        self.logger = logging.getLogger("ECMain")
        self.logger.setLevel(self._level)
        self.handlers = {}

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._format_str)
        self.handlers["console_handler"] = console_handler
        self.logger.addHandler(self.handlers["console_handler"])

    def set_level(self, level):
        self.set_level_from_env(level)

    def set_level_from_env(self, level=None):
        level = os.getenv("LOG_LEVEL") if not level else level

        if level:
            if level.lower() == "warning":
                _level = logging.WARNING
            elif level.lower() == "debug":
                _level = logging.DEBUG
            elif level.lower() == "info":
                _level = logging.INFO
            elif level.lower() == "error":
                _level = logging.ERROR
            elif level.lower() == "critical":
                _level = logging.CRITICAL

            self._set_level(_level)

    def _set_level(self, level):
        self.logger.setLevel(level)

    def enable_debug(self):
        self.logger.setLevel(logging.DEBUG)

    def disable_debug(self):
        self.logger.setLevel(self._level)

    def enable_file_logging(self, name="ec"):
        now = datetime.now().strftime("%Y%m%d")
        fname = TMP_DIR / f".{now}-{name}.log"
        file_handler = logging.FileHandler(fname)
        file_handler.setFormatter(self._format_str)
        self.handlers["file_handler"] = file_handler
        self.logger.addHandler(file_handler)
        print(f"logging to ----> [{str(fname)}]")

    def disable_file_logging(self):
        self.logger.removeHandler(self.handlers["file_handler"])

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
        sys.exit(1)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)
        sys.exit(1)


# lazy load handler
_missing = object()


class lazy_property:
    """
    Delays loading of property until first access. Credit goes to the
    Implementation in the werkzeug suite:
    http://werkzeug.pocoo.org/docs/utils/#werkzeug.utils.cached_property
    This should be used as a decorator in a class and in Evennia is
    mainly used to lazy-load handlers:
        ```python
        @lazy_property
        def attributes(self):
            return AttributeHandler(self)
        ```
    Once initialized, the `AttributeHandler` will be available as a
    property "attributes" on the object. This is read-only since
    this functionality is pretty much exclusively used by handlers.
    """

    def __init__(self, func, name=None, doc=None):
        """Store all properties for now"""
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        """Triggers initialization"""
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
        obj.__dict__[self.__name__] = value
        return value

    def __set__(self, obj, value):
        """Protect against setting"""
        handlername = self.__name__
        raise AttributeError(
            _(
                "{obj}.{handlername} is a handler and can't be set directly. "
                "To add values, use `{obj}.{handlername}.add()` instead."
            ).format(obj=obj, handlername=handlername)
        )

    def __delete__(self, obj):
        """Protect against deleting"""
        handlername = self.__name__
        raise AttributeError(
            _(
                "{obj}.{handlername} is a handler and can't be deleted directly. "
                "To remove values, use `{obj}.{handlername}.remove()` instead."
            ).format(obj=obj, handlername=handlername)
        )


def raise_error(error: Exception) -> None:
    """Raises an error."""
    logger.error(error)
    sys.exit(1)


logger = ECLogger()
logger.set_level_from_env()
