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

from argparse import ArgumentParser
from pathlib import Path

from . import logger, __version__, __packagename__
from .commands_terraform import TerraformCommands
from .commands_azure import AzureCommands
from .commands_base import VersionCommands, CleanCommands


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
        self._setup_azure_subcommand()

        return self.parse_args()

    def _setup_azure_synapse_subcommand(self, az_parser):
        # synapse
        syn_subcmd = az_parser.add_parser(
            "syn", help="Managed Azure Synapse Analytics", prefix_chars="az-syn-"
        )

        syn_parser = syn_subcmd.add_subparsers(
            help="Synapse Related Subcommands", dest="azsynsubcmd"
        )
        # --prettify
        prettify_subcmd = syn_parser.add_parser(
            "prettify",
            help="Prettify SQL/Spark Notebooks",
            prefix_chars="az-syn-prettify-",
        )

        prettify_subcmd.add_argument(
            "-n", "--name", help="name of file", dest="name", required=True
        )
        prettify_subcmd.add_argument(
            "-f",
            "--format",
            choices=["terminal", "html", "plain"],
            default="terminal",
            help="Choose output format",
            dest="format",
        )
        prettify_subcmd.add_argument(
            "-t",
            "--type",
            help="Choose type of file to parse",
            choices=["sql", "notebook"],
            dest="type",
        )

        # -- arm
        arm_subcmd = syn_parser.add_parser(
            "arm",
            help="Convert Synapse Artifacts to ARM templates",
            prefix_chars="az-syn-arm-",
        )

        arm_subcmd.add_argument(
            "-t",
            "--target-dir",
            help="Path to synapse workspace directory",
            required=True,
            dest="arm_target_dir",
        )

    def _setup_azure_subcommand(self):
        az_subcmd = self.sub_parser.add_parser(
            "az", help="Manage azure related resources", prefix_chars="az-"
        )
        az_parser = az_subcmd.add_subparsers(
            help="Available subcommands for azure.", dest="azsubcmd"
        )

        self._setup_azure_synapse_subcommand(az_parser)

    def _setup_version_subcommand(self):
        """Adds version subcommand to the parser."""
        _ = self.sub_parser.add_parser(
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
            choices=["validate", "deploy", "debug"],
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
        "az": AzureCommands,
    }
    if args.verbose:
        logger.enable_debug()
        logger.enable_file_logging()

    logger.debug(args)
    subcmd = subcmd_mapping.get(args.subcmd)

    if not subcmd:
        parser.print_help()
        return

    subcmd(args).execute()

    if args.verbose:
        logger.disable_debug()
        logger.disable_file_logging()
