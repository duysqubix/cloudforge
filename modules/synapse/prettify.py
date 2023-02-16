import argparse
import json
import pygments

from pygments.lexers import PythonLexer, SqlLexer
from pygments.formatters import Terminal256Formatter, HtmlFormatter, NullFormatter
from pathlib import Path

_supported_langs = ('python', 'sql')
_supported_types = ('sqlscript', 'notebook')
_lex_map = {'python': PythonLexer, 'sql': SqlLexer}
_format_map = {
    "terminal": Terminal256Formatter,
    "html": HtmlFormatter,
    'plain': NullFormatter
}

parser = argparse.ArgumentParser()

parser.add_argument("--name", "-n", help="name of file", required=False)
parser.add_argument("--format",
                    "-f",
                    choices=list(_format_map.keys()),
                    default="terminal")
parser.add_argument("--type", "-t", choices=_supported_types, required=False)
parser.add_argument(
    "--kv-secrets",
    required=False,
    help="valid python dictionary in JSON format [key]:[secret]")

sub_parser = parser.add_subparsers(help="subcommands", dest="subcmd")
gen_sql_subcmd = sub_parser.add_parser(
    "generate-sql-scripts",
    help="generate sql scripts based on criteria found in synapse workspace")

gen_sql_subcmd.add_argument(
    "--wks-folder-name",
    required=False,
    default=None,
    help=
    "Generate individual sql scripts from folder. If not supplied, it will generate all available sqls scripts"
)
gen_sql_subcmd.add_argument(
    "--target-dir",
    "-t",
    required=True,
    help="Target directory where synapse sql scripts are stored")

gen_sql_subcmd.add_argument(
    "--dest",
    "-d",
    required=True,
    help="Required directory where all sql files will be stored.")


class Notebook:

    def __init__(self, jdata):

        metadata = jdata['properties']['metadata']
        self.default_language = metadata['language_info']['name']
        self.spark_version = metadata['a365ComputeOptions']['sparkVersion']
        self._cells = jdata['properties']['cells']
        self.folder = jdata['properties']['folder']['name']

    def prettify(self, fmt):
        if self.default_language not in _supported_langs:
            raise AttributeError("Unsupported language: %s" %
                                 self.default_language)
        pretty_code = ""

        for cell in self._cells:
            source = "".join(cell['source'])
            pretty_source = pygments.highlight(
                source,
                lexer=_lex_map[self.default_language](),
                formatter=_format_map[fmt]())
            pretty_code += pretty_source + ("*" * 50) + "\n"

        return pretty_code


class SqlScript:

    def __init__(self, jdata):
        self.name = jdata['name']
        self.query = jdata['properties']['content']['query']
        self.folder = jdata['properties']['folder']['name']

    def prettify(self, fmt):
        return pygments.highlight(self.query,
                                  lexer=_lex_map['sql'](),
                                  formatter=_format_map[fmt]())


def main():
    args = parser.parse_args()

    if args.subcmd is not None:
        if args.subcmd == 'generate-sql-scripts':
            folder_name = args.wks_folder_name
            fmt = "plain"  # force plain parsing

            target_dir_path = Path(args.target_dir)
            dest_path = Path(args.dest)

            # create dir if not exist
            if not dest_path.is_dir():
                dest_path.mkdir()

            # iterate through all .json files
            for jsonf in target_dir_path.glob("*.json"):
                with open(jsonf, 'r') as rf:
                    jdata = json.load(rf)
                    script = SqlScript(jdata)

                    if folder_name is not None and (script.folder !=
                                                    folder_name):
                        continue

                    with open(dest_path / f"{jsonf.stem}.sql", 'w') as wf:
                        formatted_sql = script.prettify(fmt)
                        print(f"Writing {jsonf.stem} -> {dest_path}")
                        wf.write(formatted_sql)

    else:
        jdata = json.load(open(args.name))
        fmt = args.format

        if args.type == 'sqlscript':
            script = SqlScript(jdata)
            print(script.prettify(fmt))
        elif args.type == "notebook":
            nb = Notebook(jdata)
            print(nb.prettify(fmt))
        else:
            raise NotImplementedError("Unsupported type")


if __name__ == "__main__":
    main()
