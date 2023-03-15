import json
import pygments
import pyjson5 as json5
from faker import Faker
from typing import List, Dict
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode


from . import __packagename__, __version__, logger
from .azure import VALID_SYNAPSE_RESOURCES
from .azure.arm import ArmTemplate
from .azure.synapse import SynapseActionTemplate, SynManager
from .commands_base import BaseCommand
from .utils import EnvConfiguration
from .keyvault import AzureKeyVault

from pygments.formatters import find_formatter_class
from pygments.lexers import find_lexer_class_by_name
import re


class SynapseDeployArmCommand(BaseCommand):
    def setup(self):
        self.faker = Faker()

        if not self.config_file:  # assuming stuff is in osenv
            config = EnvConfiguration.load_env()
        else:
            config = EnvConfiguration.load_env(target_dir_or_file=self.config_file)

        vault_name: str = config.get("KEY_VAULT_NAME")

        auth: ClientSecretCredential = ClientSecretCredential(
            **config.get_azure_sp_creds()
        )
        tokens: Dict[str, str] = AzureKeyVault(vault_name, auth).get_secrets()

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


class SynapseConvertCommand(BaseCommand):
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


class SynapsePrettifyCommand(BaseCommand):
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
