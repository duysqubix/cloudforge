from pathlib import Path

from . import logger
from .commands_base import CleanCommands, VersionCommands
from .commands_azure import SynapsePrettifyCommand, SynapseConvertCommand
from .commands_terraform import TerraformCommands

import click


@click.group()
@click.option(
    "--verbose/--no-verbose", "-v", default=False, help="Enable verbose output"
)
@click.pass_context
def cloudforge(ctx, verbose):
    """
    CloudForge is a command-line utility for managing cloud infrastructure.
    """
    if verbose:
        logger.enable_debug()
        logger.enable_file_logging()


@cloudforge.command()
@click.option(
    "-m",
    "--module",
    type=click.Choice(["cftf", "all"], case_sensitive=True),
    help="Clean up artifacts left by CloudForge",
)
def clean(module):
    """
    Clean up artifacts left by CloudForge.

    Args:
        module: A string specifying the module to clean up. Must be "cftf" or "all".
    """
    CleanCommands(module=module).execute()


@cloudforge.command()
def version():
    """
    Display the version number of CloudForge.
    """
    VersionCommands().execute()


######## Azure CLI Commands ########
@cloudforge.group()
def az():
    """
    Azure CLI commands for CloudForge.
    """
    pass


# Synapse Commands
@az.group()
def syn():
    """
    Commands for working with Azure Synapse.
    """
    pass


@syn.command()
@click.option(
    "-n",
    "--name",
    required=True,
    help="Name of valid Azure Synapse JSON file",
)
@click.option(
    "-f",
    "--format",
    help="Choose output format",
    default="terminal",
    type=click.Choice(["terminal", "html", "plain"], case_sensitive=False),
    required=False,
)
@click.option(
    "-t",
    "--type",
    help="Choose type of file to parse",
    type=click.Choice(["sql", "notebook"], case_sensitive=True),
    required=False,
)
def prettify(name, format, type):
    """
    Prettify an Azure Synapse JSON file.

    Args:
        name: The name of the Synapse JSON file to prettify.
        format: The output format. Must be "terminal", "html", or "plain". Default is "terminal".
        type: The type of file to parse. Must be "sql" or "notebook".
    """
    SynapsePrettifyCommand(name=name, format=format, type=type).execute()


@syn.command()
@click.option(
    "-d",
    "--proj-dir",
    help="Path to Synapse Workspace directory.",
    required=False,
    type=click.Path(),
    default=Path.cwd().absolute(),
    show_default=True,
)
@click.option(
    "-f", "--format", help="Converion format", type=click.Choice(["arm"]), required=True
)
@click.option(
    "-c",
    "--config",
    help="Name of configuration file as a JSONC file. It will expect either supplied config name OR `deployment-config.jsonc` in the same directory as supplied for --proj-dir",
    required=False,
    default="deployment-config.json5",
    show_default=True,
)
@click.option(
    "-o",
    "--output",
    required=False,
    help="The name of the outputfile. Will be found in the same directory as suppled in --proj-dir",
)
def convert(proj_dir, format, config, output):
    """
    Convert Synapse Workspace Files into various formats .
    """
    proj_dir = Path(proj_dir)
    config = proj_dir / config

    SynapseConvertCommand(
        proj_dir=proj_dir, format=format, config=config, output=output
    ).execute()


# Terraform Commands
@cloudforge.command()
@click.argument(
    "action",
    nargs=1,
    type=click.Choice(["validate", "deploy", "debug"]),
    required=True,
)
@click.argument(
    "env",
    nargs=1,
    type=click.Choice(["dev", "stg", "uat", "prod"]),
    required=True,
)
@click.option(
    "-d",
    "--proj-dir",
    help="Define the project directory that holds ECTF files. Default is the current working directory.",
    default=Path.cwd().absolute(),
    type=click.Path(),
)
def tf(action, env, proj_dir):
    """
    Perform Terraform commands for CloudForge.

    Args:
        action: The action to perform. Must be "validate", "deploy", or "debug".
        env: The environment to target. Must be "dev", "stg", "uat", or "prod".
        proj_dir: The project directory that holds ECTF files. Default is the current working directory.
    """
    TerraformCommands(action=action, env=env, proj_dir=proj_dir).execute()


def execute():
    """
    Entry point for the CloudForge CLI.
    """
    cloudforge(obj={})
