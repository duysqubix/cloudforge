import typer
from enum import Enum
from pathlib import Path
from typing_extensions import Annotated
from typing import Optional, Union, List, Dict, Any, Tuple


from . import logger, ValidEnvs
from .commands_base import VersionCommands, CleanCommands
from .commands_azure import SynapsePrettifyCommand, SynapseSQLDeployCommand
from .commands_terraform import TerraformCommands

app = typer.Typer()


#### CloudForge Commands ####
@app.command("version")
def print_version():
    VersionCommands().execute()


@app.command("clean")
def clean():
    """
    Clean up artifacts
    """
    CleanCommands(module="all").execute()


#############################


## Terraform Commands ##


class TerraformActions(str, Enum):
    validate = "validate"
    deploy = "deploy"
    debug = "debug"


class TerraformEnvironments(str, Enum):
    dev = "dev"
    test = "test"
    prod = "prod"


@app.command("tf")
def terraform_main(
    env: Annotated[ValidEnvs, typer.Argument(help="The environment to deploy to")],
    action: Annotated[
        TerraformActions,
        typer.Argument(help="The action to perform on the Terraform module"),
    ] = TerraformActions.validate,
    proj_dir: Annotated[
        Path,
        typer.Option(
            "--proj-dir",
            "-d",
            exists=True,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="The directory containing the Terraform project",
        ),
    ] = Path.cwd(),
):
    TerraformCommands(action=action, env=env, proj_dir=proj_dir).execute()


########################

### Azure CLI Commands ###
azure_app = typer.Typer()
app.add_typer(azure_app, name="az")

### Synapse Commands ###
synapse_app = typer.Typer()
azure_app.add_typer(synapse_app, name="syn")


class PrettifyFormats(str, Enum):
    terminal = "terminal"
    html = "html"
    text = "text"


@synapse_app.command("prettify")
def prettify(
    name: str,
    format: PrettifyFormats = PrettifyFormats.terminal,
):
    """
    Prettify an Azure Synapse JSON file.
    """
    if "sql" in name.lower():
        type = "sqlscript"
    elif "notebook" in name.lower():
        type = "notebook"
    else:
        raise ValueError("Unsupported Synapse Notebook/Sqlscript format")
    SynapsePrettifyCommand(name=name, format=format.value, type=type).execute()


#### Synapse SQL Commands ####
synapse_sql_app = typer.Typer()
synapse_app.add_typer(synapse_sql_app, name="sql")


@synapse_sql_app.command("deploy")
def sql_deploy(
    database_uri: str,
    username: str,
    password: str,
    target_dir: Annotated[
        Path,
        typer.Option(
            "--target-dir",
            "-t",
            exists=True,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ] = Path.cwd(),
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", is_flag=True, help="Interactive mode")
    ] = False,
    db_options: Annotated[
        Optional[List[str]],
        typer.Option(
            "--db-option",
            "-o",
            help="List of db options to pass to ODBC driver",
        ),
    ] = None,
):
    """Deploy SQL scripts to dedicated SQL Pool in Azure Synapse Analytics based on JSON sqlscripts folder"""
    db_options = dict([v.split("=") for v in db_options]) if db_options else {}

    SynapseSQLDeployCommand(
        target_dir=target_dir,
        database_uri=database_uri,
        username=username,
        password=password,
        db_options=db_options,
        interactive=interactive,
    ).execute()


########################


def execute():
    app()
