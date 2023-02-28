"""This module provides a `Tokenizer` class for reading, parsing, and modifying text files.

Note:
    The `Tokenizer` class is designed to work with files in a specified directory with a given extension.

Raises:
    UnparsedTokensError: A custom exception raised when there are unparsed tokens in the parsed text content.

Attributes:
    tree (Dict[str, str]): A dictionary of file paths and contents.
    root_dir (Path): The root directory.
    dest_path (Path): The destination directory path.
    ext (str): The file extension used to filter the files.

Classes:
    Tokenizer:
        This class has the following methods:
        
        __init__(self, root_dir: Path, ext: str) -> None:
            Initializes a new `Tokenizer` instance with a given directory path and file extension.
            
        _traverse_directory(self, path: Path, ext: str) -> None:
            Recursively traverses a directory to build a tree of file paths and contents.
            
        read_root(self) -> None:
            Reads the root directory and builds a tree of file paths and contents.
            
        replace_tokens(self, tokens: Dict[str, str]) -> Dict[str, str]:
            Replaces all the specified tokens in the parsed content and returns a dictionary with updated contents.
            
        validate_tokens(self, parsed_tree: Dict[str, str]) -> Set[str]:
            Validates all the tokens in the parsed content and returns a set of validation errors.
            
        replace_and_validate_tokens(self, tokens: Dict[str, str]) -> Dict[str, str]:
            Replaces and validates all the specified tokens in the parsed content and returns a dictionary with updated contents.
            
        dump_to(self, tree: Dict[str, str], dirpath: Path, unique: bool) -> Path:
            Dumps the parsed content into a directory and returns the path of the dumped directory.
        
        Note:
            When calling the `replace_tokens`, `validate_tokens`, or `replace_and_validate_tokens` methods, the `tree` attribute of the `Tokenizer` instance must first be populated with content by calling the `read_root` method.

Methods:
    None

Constants:
    _TOKEN_RE: A regular expression object used to parse tokens from the content.
"""
from . import logger
from typing import Dict, Set
from pathlib import Path

import re
import uuid


_TOKEN_RE = re.compile(r"{{__([^\n\r\t, ]*?)__}}")

class UnparsedTokensError(Exception):
    """
    Exception raised when there are unused tokens in the parsed content.
    """
    pass

class Tokenizer:
    """A class for tokenizing and parsing the content of files in a directory.

    Args:
        root_dir (pathlib.Path): The path to the root directory to start parsing from.
        ext (str): The file extension to include for parsing.

    Attributes:
        tree (Dict[str, str]): A dictionary of file paths and contents.
        root_dir (Path): The root directory.
        dest_path (Path): The destination directory path.
        ext (str): The file extension used to filter the files.

    Raises:
        OSError: If an error occurs while traversing the directory tree.

    Methods:
        read_root(): Traverses the root directory and reads the content of the files.
        replace_tokens(tokens: Dict[str, str]) -> Dict[str, str]: Replaces tokens in the parsed content with their corresponding values.
        validate_tokens(parsed_tree: Dict[str, str]) -> Set[str]: Validates whether all the tokens in the parsed content are used.
        replace_and_validate_tokens(tokens: Dict[str, str]) -> Dict[str, str]: Replaces tokens in the parsed content and validates whether all the tokens are used.
        dump_to(tree: Dict[str, str], dirpath: Path, unique: bool) -> Path: Dumps the parsed content of files to a new directory.

    Constants:
        _TOKEN_RE: A regular expression object used to parse tokens from the content.
    """

    _TOKEN_RE = r"{{__(\w+)__}}"

    def __init__(self, root_dir: Path, ext: str) -> None:
        self.tree: Dict[str, str] = {}
        self.root_dir: Path = root_dir
        self.dest_path: Path = Path("/")
        self.ext: str = "." + ext

    def _traverse_directory(self, path: Path, ext: str) -> None:
        """A recursive function to traverse the directory tree and add the content of files to the tree.

        Args:
            path (pathlib.Path): The path of the directory to traverse.
            ext (str): The file extension to include for parsing.

        Returns:
            None
        """
        matches = path.glob("*")

        for match in matches:
            if match.is_dir() and match.name != "sandbox":
                self._traverse_directory(match, ext)

            if match.is_file() and (match.suffix == ext):
                self.tree[str(match.absolute())] = match.read_text(encoding="utf-8")

    def read_root(self) -> None:
        """Traverses the root directory and reads the content of the files.

        Raises:
            OSError: If an error occurs while traversing the directory tree.
        """
        self._traverse_directory(self.root_dir, self.ext)

    def replace_tokens(self, tokens: Dict[str, str]) -> Dict[str, str]:
        """Replaces tokens in the parsed content with their corresponding values.

        Args:
            tokens (Dict[str,str]): A dictionary of token-value pairs to replace.

        Returns:
            Dict[str, str]: A dictionary of file paths and parsed content.
        """
        tree_parsed: Dict[str, str] = {}
        for fpath, fcontent in self.tree.items():
            parsed_content = fcontent[:]  # create a copy of content to mutate
            for token, value in tokens.items():
                pattern = "{{__" + token + "__}}"
                if pattern in fcontent:
                    parsed_content = parsed_content.replace(pattern, value, -1)

            tree_parsed[fpath] = parsed_content
        return tree_parsed
        
    def validate_tokens(self, parsed_tree: Dict[str, str]) -> Set[str]:
        """Validates whether all the tokens in the parsed content are used.

        Args:
            parsed_tree (Dict[str, str]): A dictionary of file paths and parsed content.

        Returns:
            Set[str]: A set of unused tokens.
        """
        validation_errors = []
        for fcontent in parsed_tree.values():
            results = _TOKEN_RE.findall(fcontent)
            validation_errors.extend(results)
        return set(validation_errors)

    def replace_and_validate_tokens(self, tokens: Dict[str, str]) -> Dict[str, str]:
        """Replaces tokens in the parsed content and validates whether all the tokens are used.

        Args:
            tokens (Dict[str, str]): A dictionary of token-value pairs to replace.

        Raises:
            UnparsedTokensError: If there are unused tokens in the parsed content.

        Returns:
            Dict[str, str]: A dictionary of file paths and parsed content.
        """
        parsed_tree = self.replace_tokens(tokens)
        errors = self.validate_tokens(parsed_tree)
        if errors:
            raise UnparsedTokensError("Unused tokens: %s" % errors)
        return parsed_tree

    def dump_to(self, tree: Dict[str, str], dirpath: Path, unique: bool) -> Path:
        """Dumps the parsed content of files to a new directory.

        Args:
            tree (Dict[str,str]): A dictionary of file paths and parsed content.
            dirpath (pathlib.Path): The path of the directory to dump the parsed content to.
            unique (bool): Whether to append a unique identifier to the directory name.

        Returns:
            pathlib.Path: The path of the new directory where the parsed content is dumped.
        """
        if unique:
            dirpath = Path(f"{dirpath.absolute()}-{uuid.uuid4()}")

        if not dirpath.exists():
            logger.info(f"Creating directory: [{dirpath.absolute()}]")
            dirpath.mkdir()
        else:
            logger.warning("Directory already exists, overwriting.....")
            for fobj in dirpath.glob("*"):
                if fobj.is_file():
                    fobj.unlink()
                elif fobj.is_dir():
                    fobj.rmdir()

        root_dir_str = str(self.root_dir.absolute())
        for fpath, fcontent in tree.items():
            new_path = fpath.replace(root_dir_str, str(dirpath.absolute()))
            new_path_obj = Path(new_path)
            logger.info(f"[{fpath}]-->[{new_path}]")
            if not new_path_obj.is_file():
                new_path_obj.parent.mkdir(parents=True, exist_ok=True)

            new_path_obj.write_text(fcontent)
        return dirpath
            
        
if __name__ == '__main__':
    t = Tokenizer(root_dir=Path(__file__).parent.parent / ".tftest", ext="tf")
    tokens = {
        "STORAGENAME": "mystorageaccount",
        "LOCATION": "southcentralus",
        "OTHER": "yup"
    }
    t.read_root()
    parsed_tree = t.replace_and_validate_tokens(tokens)
    t.dump_to(parsed_tree, Path("/tmp/.terraform-py"), unique=True)
