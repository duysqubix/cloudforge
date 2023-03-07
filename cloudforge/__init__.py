from pathlib import Path
from datetime import datetime
import logging
import tempfile

__packagename__ = "cloudforge"
__version__ = "0.8.0-dev"

VALID_ENVS = ["dev", "stg", "uat", "prod"]

TMP_DIR = Path(tempfile.gettempdir())
TFPY_DIR_BASE_NAME = ".terraform-py"
TMP_PATH = TMP_DIR / TFPY_DIR_BASE_NAME


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

    def setLevel(self, level):
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

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


logger = ECLogger()
