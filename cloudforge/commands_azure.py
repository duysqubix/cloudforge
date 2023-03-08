from pygments.lexers import find_lexer_class_by_name
from pygments.formatters import find_formatter_class

from typing import Any, Dict
from . import logger, __version__, __packagename__
from .commands_base import BaseCommand
from .azure.synapse import SynapseActionTemplate


import pyjson5 as json5
import json
import pygments
import re


class SynapseConvertCommand(BaseCommand):
    def execute(self) -> None:
        if self.format == "arm":
            self._execute_convert_to_arm()

    def _execute_convert_to_arm(self):
        syn_workspace_dir = self.proj_dir
        config_file = self.config

        if not syn_workspace_dir.is_dir():
            raise FileNotFoundError("Synapse Workspace not a valid directory")

        if not config_file.is_file():
            raise FileNotFoundError(
                "Deployment configuration file not valid or missing"
            )

        config = json5.load(open(config_file))

        syn_action_template = SynapseActionTemplate(config)

        print(syn_action_template._map)

        return
        result = syn_action_template.process_synapse_workspace(
            str(syn_workspace_dir), inplace=replace
        )

        pretty_print_modified_actions(result)

        # transform Synapse JSON to ARM file

        synm = SynManager(workspace_name="amerivetsynapseprod")  # change me
        valid_resources = [
            "linkedService",
            "credential",
            "trigger",
            "dataset",
            "notebook",
            "integrationRuntime",
            "pipeline",
        ]

        defaults: List[str] = []
        for rtype in valid_resources:
            for jfile in (syn_workspace_dir / rtype).glob("*.json"):
                if "WorkspaceDefault" in jfile.name:
                    defaults.append(jfile.name.replace(".json", ""))

                with open(jfile, "r") as f:
                    jdata = json.load(f)

                    synm.add_resource(rtype, jdata)
        armt: ArmTemplate = synm.convert_to_arm_objs()

        dest_arm_path = self.output

        with open(dest_arm_path, "w") as f:
            jdata: str = json.dumps(armt.to_arm_json(), indent=2)  # type: ignore

            ##### final pass through -- rename ALL Workspace names to the supplied one -- needed for dynamic environment change
            for default in defaults:
                _d = default.split("WorkspaceDefault")
                _d[0] = args.workspace_name
                modified = "-WorkspaceDefault".join(_d)

                jdata = re.sub(default, modified, jdata)

            f.write(jdata)
            # json.dump(armt.to_arm_json(), f, indent=2)  #type: ignore


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
