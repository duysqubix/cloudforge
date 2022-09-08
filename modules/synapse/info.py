import argparse
import json
import pygments

from pygments.lexers import PythonLexer, SqlLexer
from pygments.formatters import Terminal256Formatter, HtmlFormatter

_supported_langs = ('python', 'sql')
_supported_formats = ('terminal', 'html')
_supported_types = ('sqlscript', 'notebook')
_lex_map = {'python': PythonLexer, 'sql': SqlLexer}
_format_map = {"terminal": Terminal256Formatter, "html": HtmlFormatter}

parser = argparse.ArgumentParser()

parser.add_argument("--name", "-n", help="name of file", required=True)
parser.add_argument("--format",
                    "-f",
                    choices=_supported_formats,
                    default="terminal")
parser.add_argument("--type", "-t", choices=_supported_types, required=True)


class Notebook:

    def __init__(self, jdata):

        metadata = jdata['properties']['metadata']
        self.default_language = metadata['language_info']['name']
        self.spark_version = metadata['a365ComputeOptions']['sparkVersion']
        self._cells = jdata['properties']['cells']

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

    def prettify(self, fmt):
        return pygments.highlight(self.query,
                                  lexer=_lex_map['sql'](),
                                  formatter=_format_map[fmt]())


def main():
    args = parser.parse_args()

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
