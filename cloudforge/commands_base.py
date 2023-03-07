from argparse import Namespace

from . import TMP_PATH, logger, TMP_DIR, __version__, __packagename__

import shutil


class BaseCommand:
    """Base class for handling commands."""

    def __init__(self, args: Namespace, skip_setup: bool = False) -> None:
        """Initializes the BaseCommand class.

        Args:
            args (Namespace): The arguments for the command.
            skip_setup (bool): Whether to skip the setup method.
        """
        self._args: Namespace = args
        logger.debug(self._args)

        if not skip_setup:
            self.setup()

    def setup(self) -> None:
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

    def setup(self) -> None:
        """Sets up the CleanCommands class."""
        self.module_to_clean: str = self._args.module

    def execute(self) -> None:
        """Executes the clean command."""
        if self.module_to_clean == "all":
            self._clean_up_ectf_files()

        elif self.module_to_clean == "ectf":
            self._clean_up_ectf_files()

    def _clean_up_ectf_files(self) -> None:
        """Cleans up the ectf files."""
        for fobj in TMP_DIR.glob("*"):
            if "terraform" in fobj.name:
                if fobj.is_dir():
                    logger.warning(f"Removing {fobj}")
                    shutil.rmtree(fobj)

                if fobj.is_file():
                    logger.warning(f"Removing {fobj}")
                    fobj.unlink()
