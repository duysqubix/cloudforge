"""
This module provides a `Tokenizer` class, which is used for reading, parsing, and modifying text files.

.. note::
    The `Tokenizer` class is designed to work with files in a specified directory with a given extension.

:class:`UnparsedTokensError`
---------------------------
This is a custom exception raised when there are unparsed tokens in the parsed text content.

:class:`Tokenizer`
-------------------
This class has the following methods:

- `__init__(root_dir: Path, ext: str) -> None`: initializes a new `Tokenizer` instance with a given directory path and file extension.
- `_traverse_directory(path: Path, ext: str) -> None`: recursively traverses a directory to build a tree of file paths and contents.
- `read_root() -> None`: reads the root directory and builds a tree of file paths and contents.
- `replace_tokens(tokens: Dict[str, str]) -> Dict[str, str]`: replaces all the specified tokens in the parsed content and returns a dictionary with updated contents.
- `validate_tokens(parsed_tree: Dict[str, str]) -> Set[str]`: validates all the tokens in the parsed content and returns a set of validation errors.
- `replace_and_validate_tokens(tokens: Dict[str, str]) -> Dict[str, str]`: replaces and validates all the specified tokens in the parsed content and returns a dictionary with updated contents.
- `dump_to(tree: Dict[str, str], dirpath: Path, unique: bool) -> Path`: dumps the parsed content into a directory and returns the path of the dumped directory.

The `Tokenizer` class also has the following attributes:

- `tree: Dict[str, str]`: a dictionary of file paths and contents.
- `root_dir: Path`: the root directory.
- `dest_path: Path`: the destination directory path.
- `ext: str`: the file extension used to filter the files.

The module also has a regular expression object called `_TOKEN_RE`, which is used to parse tokens from the content.

.. note::
    When calling the `replace_tokens`, `validate_tokens`, or `replace_and_validate_tokens` methods, the `tree` attribute of the `Tokenizer` instance must first be populated with content by calling the `read_root` method.

"""

from typing import Dict, Set
from pathlib import Path

import re
import logging 
import uuid


_TOKEN_RE = re.compile(r"{{__([^\n\r\t, ]*?)__}}")

class UnparsedTokensError(Exception):
    """
    Exception raised when there are unused tokens in the parsed content.
    """
    pass

class Tokenizer:
    """
    A class for tokenizing and parsing the content of files in a directory.

    :param root_dir: The path to the root directory to start parsing from.
    :type root_dir: :class:`pathlib.Path`
    :param ext: The file extension to include for parsing.
    :type ext: str
    """
    def __init__(self, root_dir: Path, ext: str) -> None:
        self.tree: Dict[str,str] = {}
        self.root_dir: Path = root_dir
        self.dest_path: Path = Path("/")
        self.ext: str = "."+ext
        
    def _traverse_directory(self, path: Path, ext: str):
        """
        A recursive function to traverse the directory tree and add the content of files to the tree.

        :param path: The path of the directory to traverse.
        :type path: :class:`pathlib.Path`
        :param ext: The file extension to include for parsing.
        :type ext: str
        """
        matches = path.glob("*")
        
        for match in matches:
            if match.is_dir() and match.name != "sandbox":
                self._traverse_directory(match, ext)
            
            if match.is_file() and (match.suffix == ext):
                self.tree[str(match.absolute())] = match.read_text(encoding='utf-8')
    
    def read_root(self):
        """
        Traverses the root directory and reads the content of the files.

        :raises: OSError
        """
        self._traverse_directory(self.root_dir, self.ext)
        
    def replace_tokens(self, tokens: Dict[str,str]):
        """
        Replaces tokens in the parsed content with their corresponding values.

        :param tokens: A dictionary of token-value pairs to replace.
        :type tokens: dict
        :returns: A dictionary of file paths and parsed content.
        :rtype: dict
        """
        tree_parsed: Dict[str, str] = {}
        for fpath, fcontent in self.tree.items():
            parsed_content = fcontent[:]    # create a copy of content to mutate
            for token, value in tokens.items():
                pattern = r"{{__"+token+r"__}}"
                if pattern in fcontent:
                    parsed_content = parsed_content.replace(pattern, value, -1)

            tree_parsed[fpath] = parsed_content
        return tree_parsed
        
    def validate_tokens(self, parsed_tree: Dict[str, str]) -> Set[str]:
        """
        Validates whether all the tokens in the parsed content are used.

        :param parsed_tree: A dictionary of file paths and parsed content.
        :type parsed_tree: dict
        :returns: A set of unused tokens.
        :rtype: set
        """
        validation_errors = []
        for fcontent in parsed_tree.values():
            results = _TOKEN_RE.findall(fcontent)
            validation_errors.extend(results)
        return set(validation_errors)
    
    def replace_and_validate_tokens(self, tokens: Dict[str,str]):
            """
            Replaces tokens in the parsed content and validates whether all the tokens are used.

            :param tokens: A dictionary of token-value pairs to replace.
            :type tokens: dict
            :raises: UnparsedTokensError
            :returns: A dictionary of file paths and parsed content.
            :rtype: dict
            """
            parsed_tree = self.replace_tokens(tokens)
            errors = self.validate_tokens(parsed_tree)
            if errors:
                raise UnparsedTokensError("Unused tokens: %s" % errors)
            return parsed_tree
                
    def dump_to(self, tree: Dict[str,str], dirpath: Path, unique: bool) -> Path:
        """
        Dumps the parsed content of files to a new directory.

        :param tree: A dictionary of file paths and parsed content.
        :type tree: dict
        :param dirpath: The path of the directory to dump the parsed content to.
        :type dirpath: :class:`pathlib.Path`
        :param unique: Whether to append a unique identifier to the directory name.
        :type unique: bool
        :returns: The path of the new directory where the parsed content is dumped.
        :rtype: :class:`pathlib.Path`
        """
        if unique:
            dirpath = Path(f"{dirpath.absolute()}-{uuid.uuid4()}")
        
        if not dirpath.exists():
            logging.info(f"Creating directory: [{dirpath.absolute()}]")
            dirpath.mkdir()
        else:
            logging.warning("Directory already exists, overwriting.....")
            for fobj in dirpath.glob("*"):
                if fobj.is_file():
                    fobj.unlink()
                elif fobj.is_dir():
                    fobj.rmdir()
                    
        root_dir_str = str(self.root_dir.absolute())
        for fpath, fcontent in tree.items():
            new_path = fpath.replace(root_dir_str,str(dirpath.absolute()))
            new_path_obj = Path(new_path)
            logging.info(f"[{fpath}]-->[{new_path}]")
            if not new_path_obj.is_file():
                new_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            new_path_obj.write_text(fcontent)
        return dirpath


            
        
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    t = Tokenizer(root_dir=Path(__file__).parent.parent / ".tftest", ext="tf")
    tokens = {
        "STORAGENAME": "mystorageaccount",
        "LOCATION": "southcentralus",
        "OTHER": "yup"
    }
    t.read_root()
    parsed_tree = t.replace_and_validate_tokens(tokens)
    t.dump_to(parsed_tree, Path("/tmp/.terraform-py"), unique=True)
