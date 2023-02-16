"""
The `utils` module provides the `EnvConfiguration` class, which represents a configuration object for environment variables. 

The `EnvConfiguration` class provides methods to read and parse a configuration file or use environment variables, and to retrieve a dictionary of key-value pairs that have keys containing the substring "ARM_".

Example Usage:
    ec = EnvConfiguration("config.env")
    ec.read_and_parse()
    arms = ec.get_arms()
"""

from typing import Dict, Optional
from pathlib import Path
from copy import deepcopy

import os

class EnvConfiguration:
    """
    Represents a configuration object for environment variables.

    :param fpath: The path to the configuration file. If `None`, uses environment variables instead.
    :type fpath: str, optional
    """
    def __init__(self, fpath: Optional[str]=None) -> None:
        """
        Initializes a new instance of the `EnvConfiguration` class.

        :param fpath: The path to the configuration file. If `None`, uses environment variables instead.
        :type fpath: str, optional
        """
        self.fpath: Optional[Path] = Path(fpath) if fpath is not None else None
        self.key_pairs: Dict[str, str] = dict()
        
    def read_and_parse(self):
        """
        Reads and parses the configuration file, or uses environment variables if no file is specified.
        """
        self.key_pairs.clear()
        if not self.fpath:
            # read from os.env and store entire env as dict
            # this will more than likely include variables not of interest
            self.key_pairs = deepcopy(dict(os.environ))
        else:
            with open(self.fpath, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    key, value = line.split("=", maxsplit=1)
                    self.key_pairs[key] = value 

    def get_arms(self) -> Dict[str,str]:
        """
        Returns a dictionary of key-value pairs that have keys containing the substring "ARM_".

        :return: A dictionary of key-value pairs that have keys containing the substring "ARM_".
        :rtype: dict
        """
        return dict(filter(lambda item: "ARM_" in item[0], self.key_pairs.items()))
    
    def get(self, key):
        """wrapper to get value from key, returns None if it can't find anything"""
        return self.key_pairs[key]

