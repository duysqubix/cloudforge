from . import TMP_PATH, logger, TMP_DIR, __version__, __packagename__

import shutil
import sys


class BaseCommand:
    """Base class for handling commands."""

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            self.__dict__[k] = v

        self.setup()

    def setup(self):
        pass

    def execute(self) -> None:
        pass
    

class VersionCommands(BaseCommand):
    """Class for handling version commands."""

    def execute(self) -> None:
        """Executes the version command."""
        print(f"Running {__packagename__}: {__version__}")


class CleanCommands(BaseCommand):
    """Class for handling cleaning commands.

    Attributes:
        module_to_clean (str): The module to clean.
    """

    def execute(self) -> None:
        """Executes the clean command."""
        print("HELLO", self.module)
        if self.module == "all":
            logger.debug("Cleaning all")
            self._clean_up_cftf_files()
            self._clean_up_synapse_files()

        elif self.module == "cftf":
            logger.debug("Cleaning cftf files")

            self._clean_up_cftf_files()

        elif self.module == "syn":
            logger.debug("Cleaning synapse files")
            self._clean_up_synapse_files()

    def _clean_up_synapse_files(self) -> None:
        """Cleans up related synapse artifacts"""
        for fobj in TMP_DIR.glob("*"):
            if "synapse" in fobj.name:
                if fobj.is_dir():
                    logger.warning(f"Removing {fobj}")
                    shutil.rmtree(fobj)

                if fobj.is_file():
                    logger.warning(f"Removing {fobj}")
                    fobj.unlink()

    def _clean_up_cftf_files(self) -> None:
        """Cleans up the cftf files."""
        for fobj in TMP_DIR.glob("*"):
            if "terraform" in fobj.name:
                if fobj.is_dir():
                    logger.warning(f"Removing {fobj}")
                    shutil.rmtree(fobj)

                if fobj.is_file():
                    logger.warning(f"Removing {fobj}")
                    fobj.unlink()
