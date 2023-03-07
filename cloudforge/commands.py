"""
This module provides the following command-line utilities:

- `ec tf action env`
- `ec syn arm --options`
- `ec syn prettify --options`

The module includes the following classes:

- `BaseCommand`: A base class for handling commands.
- `VersionCommands`: A class for handling version commands.
- `CleanCommands`: A class for handling cleaning commands.
- `TerraformCommands`: A class for handling Terraform commands.

The module also includes the following functions:

- `execute()`: Parses the command-line arguments and executes the corresponding command.

Example Usage:

```python
from cloudforge import execute

execute()
```
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from azure.identity import ClientSecretCredential
from typing import Tuple, Dict, Union

from . import TMP_PATH, logger, TMP_DIR, __version__, __packagename__
from .tokenizer import Tokenizer
from .terraform_install import TerraformInstaller, __TERRAFORM_VERSION__
from .terraform_exec import Terraform
from .keyvault import AzureKeyVault
from .utils import EnvConfiguration

import shutil
import platform
import os
import sys


class BaseCommand:
    """Base class for handling commands."""

    def __init__(self, args: Namespace, skip_setup: bool = False) -> None:
        """Initializes the BaseCommand class.

        Args:
            args (Namespace): The arguments for the command.
            skip_setup (bool): Whether to skip the setup method.
        """
        self._args: Namespace = args

        if not skip_setup:
            self.setup()

    def setup(self) -> None:
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


class TerraformCommands(BaseCommand):
    """Class for handling Terraform commands.

    Attributes:
        targeted_action (str): The targeted Terraform action.
        tokenizer (Tokenizer): The Tokenizer object used to replace and validate tokens.
        config (EnvConfiguration): The EnvConfiguration object to load the environment configuration.
        backend_config (Dict[str, str]): The backend configuration for Terraform.
        arm_config (Dict[str, str]): The ARM configuration for Terraform.
        tmp_dir (Path): The temporary directory for the parsed Terraform files.
    """

    def setup(self) -> None:
        """Sets up the TerraformCommands class."""
        self.targeted_action: str = self._args.action

        self.tokenizer: Tokenizer = Tokenizer(self._args.proj_dir, "tf")
        self.tokenizer.read_root()

        self.config: EnvConfiguration = EnvConfiguration.load_env(
            self._args.env, self._args.proj_dir
        )

        vault_name: str = self.config.get("KEY_VAULT_NAME")

        auth: ClientSecretCredential = ClientSecretCredential(
            **self.config.get_terraform_creds()
        )
        tokens: Dict[str, str] = AzureKeyVault(vault_name, auth).get_secrets()

        # get secrets from Key Vault
        parsed_tree = self.tokenizer.replace_and_validate_tokens(tokens)

        self.tmp_dir: Path = self.tokenizer.dump_to(
            tree=parsed_tree, dirpath=TMP_PATH, unique=True
        )

        self.backend_config: Dict[str, str] = {
            "storage_account_name": self.config.get("STORAGE_ACCOUNT_NAME"),
            "sas_token": self.config.get("SAS_TOKEN"),
            "key": self.config.get("TF_KEY"),
            "container_name": self.config.get("CONTAINER_NAME"),
        }

        self.arm_config: Dict[str, str] = {
            "ARM_CLIENT_ID": self.config.get("ARM_CLIENT_ID"),
            "ARM_CLIENT_SECRET": self.config.get("ARM_CLIENT_SECRET"),
            "ARM_TENANT_ID": self.config.get("ARM_TENANT_ID"),
            "ARM_SUBSCRIPTION_ID": self.config.get("ARM_SUBSCRIPTION_ID"),
        }

    def _run_tf_cmd(self, cmd, **kwargs) -> None:
        """Runs a Terraform command.

        Args:
            cmd (Callable): The Terraform command to run.
            **kwargs: The keyword arguments to pass to the command.

        Raises:
            SystemExit: If the Terraform command raises an error.
        """
        options = kwargs.copy()

        options["raise_on_error"] = False
        options["capture_output"] = True

        ret_code, msg, err_msg = cmd(**options)
        if ret_code != 0:
            self._clean_up()
            logger.error(f"CMD: tf.{cmd.__name__}() raised error.. aborting")
            logger.error(err_msg)
            sys.exit(ret_code)
        logger.info(msg)

    def _clean_up(self) -> None:
        """Cleans up the temporary directory."""
        logger.warning(f"Removing directory: {self.tmp_dir.absolute()}")
        shutil.rmtree(self.tmp_dir)  # clean up

    def execute(self) -> None:
        """Executes the targeted Terraform action."""
        if self.targeted_action in ("validate", "deploy"):
            with TerraformInstaller(
                keep_binary=False, version=__TERRAFORM_VERSION__
            ) as tf_installer:
                self.config.ensure_arms_in_env()  # this ensures arm credentials are set in os environment, used by Terraform binary
                ectf_dir = str(self.tmp_dir.absolute())

                tf = Terraform(
                    terraform_bin_path=tf_installer.bin_path,
                    working_dir=ectf_dir,
                    is_env_vars_included=True,
                )

                self._run_tf_cmd(
                    tf.init,
                    backend_config=self.backend_config,
                    backend=True,
                    reconfigure=False,
                )

                if self.targeted_action == "validate":
                    self._run_tf_cmd(tf.validate)
                    self._run_tf_cmd(tf.plan, detailed_exitcode=False)

                if self.targeted_action == "deploy":
                    self._run_tf_cmd(tf.apply, skip_plan=True)

            self._clean_up()

        elif self.targeted_action == "debug":
            self._handle_debug_action()

    def _handle_debug_action(self) -> None:
        """Handles the debug action."""
        if platform.system() != "Linux":
            raise OSError(
                "Debug command does not work in a windows environment, please switch to an OS that supports Bash Scripting"
            )

        init_fname: str = "init.sh"
        wrapper_fname: str = "terraform.sh"

        prefix_str: str = ""
        for k, v in self.arm_config.items():
            prefix_str += f"{k}={v} "

        backend_configs: str = ""
        for k, v in self.backend_config.items():
            if k == "sas_token":
                v = f'"{v}"'
            backend_configs += f"-backend-config={k}={v} "

        init_path: Path = self.tmp_dir / init_fname
        wrapper_path: Path = self.tmp_dir / wrapper_fname

        with open(init_path, "w") as init_f:
            script_str: str = (
                "#!/usr/bin/env bash\n\n"
                + f"{prefix_str}terraform init {backend_configs}"
            )
            init_f.write(script_str)
            logger.info(f"Writing to: {init_path}")

        with open(wrapper_path, "w") as wrapper_f:
            script_str2: str = "#!/usr/bin/env bash\n\n" + f"{prefix_str}terraform $@"
            wrapper_f.write(script_str2)
            logger.info(f"Writing to: {wrapper_path}")

        os.chmod(init_path, 0o700)
        os.chmod(wrapper_path, 0o700)
        logger.warning(f"Debug environment created in: {self.tmp_dir}")
        logger.warning("Please take caution and remove directory when done.")


class CloudForgeArgParser(ArgumentParser):
    """Argument parser for CloudForge CLI.

    Attributes:
        sub_parser (argparse._SubParsersAction): The subparsers object to handle subcommands.
    """

    def init(self):
        """Parses the command-line arguments and returns the arguments as a Namespace object.

        Returns:
            Namespace: An object containing the command-line arguments.
        """
        self.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose mode.",
        )

        self.sub_parser = self.add_subparsers(
            help="Available subcommands.",
            dest="subcmd",
        )

        self._setup_terraform_subcommand()
        self._setup_clean_subcommand()
        self._setup_version_subcommand()

        return self.parse_args()

    def _setup_version_subcommand(self):
        """Adds version subcommand to the parser."""
        version_subcmd = self.sub_parser.add_parser(
            "version",
            help="Versioning information.",
            prefix_chars="version-",
        )

    def _setup_terraform_subcommand(self):
        """Adds terraform subcommand to the parser."""
        tf_subcmd = self.sub_parser.add_parser(
            "tf",
            help="Terraform available commands.",
            prefix_chars="tf-",
        )

        tf_subcmd.add_argument(
            "action",
            choices=["validate", "deploy", "debug", "clean"],
            help="Choose an action.",
        )

        tf_subcmd.add_argument(
            "env",
            choices=["dev", "stg", "uat", "prod"],
            help="Choose a targeted environment.",
        )

        tf_subcmd.add_argument(
            "-d",
            "--proj-dir",
            default=str(Path.cwd().absolute()),
            type=lambda x: Path(x),
            help=f"Define the project directory that holds ECTF files. Default: {str(Path.cwd().absolute())}",
        )

    def _setup_clean_subcommand(self):
        """Adds clean subcommand to the parser."""
        clean_subcmd = self.sub_parser.add_parser(
            "clean",
            help="Helper utilities to clean up artifacts left by ec.",
            prefix_chars="c-",
        )

        clean_subcmd.add_argument(
            "module",
            choices=["ectf", "all"],
            help="Clean up artifacts left by ec.",
        )


def execute():
    parser = CloudForgeArgParser(prog="cloudforge")
    args = parser.init()

    subcmd_mapping = {
        "tf": TerraformCommands,
        "clean": CleanCommands,
        "version": VersionCommands,
    }

    if args.verbose:
        logger.enable_debug()
        logger.enable_file_logging()

    subcmd = subcmd_mapping.get(args.subcmd)

    if not subcmd:
        parser.print_help()
        return

    subcmd(args).execute()

    if args.verbose:
        logger.disable_debug()
        logger.disable_file_logging()
