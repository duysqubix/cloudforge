from pygments.lexers import find_lexer_class_by_name
from pygments.formatters import find_formatter_class

from . import TMP_PATH, logger, TMP_DIR, __version__, __packagename__
from .commands_base import BaseCommand


import json
import pygments


class AzureCommands(BaseCommand):
    __mapping__ = {"syn": "SynapseCommands"}

    def execute(self):
        subcmd = self._args.azsubcmd

        azsubcmd_callable = eval(self.__mapping__[subcmd])
        azsubcmd_callable(self._args).execute()


class SynapseCommands(AzureCommands):
    def _execute_prettify_cmd(self):
        format_ = self._args.format
        name = self._args.name
        type_ = self._args.type

        jdata = json.load(open(name, "r"))

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

        type_ = type_ if self._args.type is None else self._args.type

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

    def execute(self):
        syn_subcmd = self._args.azsynsubcmd

        if syn_subcmd == "prettify":
            self._execute_prettify_cmd()
            return
        elif syn_subcmd == "":
            return

        print("Please specificy Synapse subcommand")
