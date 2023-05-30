import json
import pygments
import os
import pyjson5 as json5
from faker import Faker
from typing import List, Dict, Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from pathlib import Path

from . import (
    __packagename__,
    __version__,
    logger,
    lazy_property,
    SYNAPSE_ANALYTICS_DB_SETUP_SCRIPT_NAME,
)
from .azure import VALID_SYNAPSE_RESOURCES
from .azure.arm import ArmTemplate
from .azure.synapse import SynapseActionTemplate, SynManager
from .commands_base import BaseCommand
from .utils import EnvConfiguration
from .keyvault import AzureKeyVault
from .tokenizer import Tokenizer
from .mssql import SynapseAnalyticsConnection, Migration

from pygments.formatters import find_formatter_class
from pygments.lexers import find_lexer_class_by_name
import re


class AzureBaseCommand(BaseCommand):
    def __init__(self, **kwargs) -> None:
        self.env = None
        self.config_file = None
        super().__init__(**kwargs)

        self.setup()

    @lazy_property
    def key_vault_secrets(self):
        if not self.env:
            self.raise_error(ValueError("Environment not specified"))

        if not self.config:  # assuming stuff is in osenv
            config = EnvConfiguration.load_env()
        else:
            config = EnvConfiguration.load_env(target_dir_or_file=self.config)

        vault_name: Optional[str] = config.get("KEY_VAULT_NAME")

        auth: ClientSecretCredential = ClientSecretCredential(
            **config.get_azure_sp_creds()
        )
        tokens: Dict[str, str] = AzureKeyVault(vault_name, auth).get_secrets()
        return tokens, config


class SynapseDeployArmCommand(AzureBaseCommand):
    def setup(self):
        self.faker = Faker()
        tokens, config = self.get_key_vault_secrets()

        self.subscription_id = config.get("ARM_SUBSCRIPTION_ID")
        self.resource_group_name = tokens.get("ResourceGroupName")
        self.deployment_name = self._create_deployment_name()
        self.creds = auth

    def _create_deployment_name(self):
        return (
            f"{self.faker.color_name()}-{self.faker.city_suffix()}-{self.faker.bban()}"
        )

    def execute(self) -> None:
        if not self.arm_file.is_file():
            raise FileNotFoundError("Arm template file not found")
        resource_management_client = ResourceManagementClient(
            self.creds, self.subscription_id
        )

        template = open(self.arm_file, "r").read()

        deployment_properties = {
            "properties": {
                "mode": DeploymentMode.INCREMENTAL,
                "template": template,
                "parameters": {},
            }
        }
        print(json.dumps(deployment_properties, indent=2))
        # deployment_async_op = (
        #     resource_management_client.deployments.begin_create_or_update(
        #         self.resource_group_name, self.deployment_name, deployment_properties
        #     )
        # )
        # deployment_async_op.wait()


class SynapseConvertCommand(AzureBaseCommand):
    def execute(self) -> None:
        if self.format == "arm":
            self._execute_convert_to_arm()

    def _execute_convert_to_arm(self):
        config_file = self.config

        if not self.proj_dir.is_dir():
            raise FileNotFoundError("Synapse Workspace not a valid directory")

        if not config_file.is_file():
            raise FileNotFoundError(
                "Deployment configuration file not valid or missing"
            )

        config = json5.load(open(config_file))

        syn_action_template = SynapseActionTemplate(
            config, syn_dir=self.proj_dir
        ).parse()

        resp = syn_action_template.process(for_env=self.env)
        # transform Synapse JSON to ARM file
        syn_workspace_name = resp["name"]
        syn_dir = resp["tmpdir"]
        synm = SynManager(workspace_name=syn_workspace_name, syn_dir=syn_dir)

        armt: ArmTemplate = synm.convert_to_arm_objs()

        if self.output:
            output_path = self.output_dir / self.output
        else:
            output_path = self.output_dir / "synapseArm.json"

        jdata: str = json.dumps(armt.to_arm_json(), indent=2)  # type: ignore

        ##### final pass through -- rename ALL Workspace names to the supplied one -- needed for dynamic environment change
        for default in defaults:
            _d = default.split("WorkspaceDefault")
            _d[0] = syn_workspace_name
            modified = "-WorkspaceDefault".join(_d)

            jdata = re.sub(default, modified, jdata)

        with open(output_path, "w") as f:
            logger.debug(f"Writing final dynamic ARM to {output_path}")
            f.write(jdata)


class SynapseSQLDeployCommand(AzureBaseCommand):
    def setup(self) -> None:
        self.target_dir = Path(self.target_dir)
        # self.tokens = self.key_vault_secrets
        # self.tokenizer: Tokenizer = Tokenizer(self.target_dir, "json")
        # self.tokenizer.read_root()

    """Deploy SQL Scripts"""

    def execute(self):
        target_dir = self.target_dir
        username = self.username
        password = self.password
        options = self.db_options

        if not target_dir.is_dir():
            logger.error("Target directory is not a valid directory")

        db_con = SynapseAnalyticsConnection(
            database_uri=self.database_uri,
            username=username,
            password=password,
            **options,
        )

        scripts_path = Path(target_dir)

        scripts = []
        for script in scripts_path.glob("*.json"):
            with open(script, "r") as f:
                jdata = json.load(f)
                query = jdata["properties"]["content"]["query"]
                folder = jdata.get("properties", {}).get("folder", {}).get("name")
                database = (
                    jdata.get("properties", {})
                    .get("content", {})
                    .get("currentConnection", {})
                    .get("databaseName")
                )

                keep = False
                if "etl_objects" in folder:
                    keep = True

                if "migrations" in folder:
                    keep = True

                if not keep:
                    logger.debug(
                        f"Skipping {script.name} as it is not in a valid folder"
                    )
                    continue

                scripts.append(
                    {
                        "query": query,
                        "name": script.name.split(".")[0],
                        "folder": folder,
                        "database": database,
                    }
                )

        if not scripts:
            logger.error(ValueError("No valid scripts found in `%s`" % target_dir))

        migrations = []
        etl_objects = []
        initial_setup = None
        for script in scripts:
            if script["folder"] == "migrations":
                migrations.append(script)
            if "etl_objects" in script["folder"]:
                if script["name"] == SYNAPSE_ANALYTICS_DB_SETUP_SCRIPT_NAME:
                    initial_setup = script
                else:
                    etl_objects.append(script)

        Migration(
            db_con=db_con,
            initial_setup=initial_setup,
            migrations=migrations,
            etl_objects=etl_objects,
        ).deploy(interactive=self.interactive)


class SynapsePrettifyCommand(AzureBaseCommand):
    def execute(self):
        """Prettify Synapse Notebook or Sqlscript."""
        format_ = self.format
        name = self.name
        type_ = self.type

        with open(name, "r") as f:
            jdata = json.load(f)

        lang = (
            jdata.get("properties", {})
            .get("metadata", {})
            .get("language_info", {})
            .get("name")
        )
        type_ = "notebook"
        if lang is None:
            lang = (
                jdata.get("properties", {})
                .get("content", {})
                .get("metadata", {})
                .get("language")
            )
            type_ = "sqlscript"

        if lang is None:
            logger.critical("Unsupported Synapse Notebook/Sqlscript format")
            raise ValueError("Unsupported Synapse Notebook/Sqlscript format")

        type_ = type_ if self.type is None else self.type

        logger.debug(
            (
                f"\nlang: {lang}\n"
                + f"format_: {format_}\n"
                + f"type_: {type_}\n"
                + f"name: {name}"
            )
        )
        if type_ == "sqlscript":
            query = jdata["properties"]["content"]["query"]
            prettied_query = pygments.highlight(
                query,
                lexer=find_lexer_class_by_name(lang)(),
                formatter=find_formatter_class(format_)(),
            )
            print(prettied_query)

        if type_ == "notebook":
            cells = jdata["properties"]["cells"]
            pretty_code = ""
            for cell in cells:
                source = "".join(cell["source"])
                prettied_source = pygments.highlight(
                    source,
                    lexer=find_lexer_class_by_name(lang)(),
                    formatter=find_formatter_class(format_)(),
                )
                pretty_code += prettied_source + ("*" * 50) + "\n"

            print(pretty_code)
