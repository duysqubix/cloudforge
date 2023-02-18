"""
The utils module provides the EnvConfiguration class, which represents a configuration object for environment variables.

The EnvConfiguration class provides methods to read and parse a configuration file or use environment variables, and to retrieve a dictionary of key-value pairs that have keys containing the substring "ARM_".

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
    Args:
        fpath (str, optional): The path to the configuration file. If `None`, uses environment variables instead.

    Attributes:
        fpath (Path, optional): The path to the configuration file. If `None`, uses environment variables instead.
        key_pairs (Dict[str, str]): A dictionary of key-value pairs.

    """
    def __init__(self, fpath: Optional[str] = None) -> None:
        """
        Initializes a new instance of the `EnvConfiguration` class.

        Args:
            fpath (str, optional): The path to the configuration file. If `None`, uses environment variables instead.
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

    def get_arms(self) -> Dict[str, str]:
        """
        Returns a dictionary of key-value pairs that have keys containing the substring "ARM_".

        Returns:
            dict: A dictionary of key-value pairs that have keys containing the substring "ARM_".
        """
        return dict(filter(lambda item: "ARM_" in item[0], self.key_pairs.items()))

    def get(self, key):
        """Wrapper to get value from key, returns None if it can't find anything

        Args:
            key: The key of the value to retrieve.

        Returns:
            str: The value of the key or `None` if it can't find anything.
        """
        return self.key_pairs[key]
    
    def get_terraform_creds(self):
        arms = self.get_arms()
        client_id = arms["ARM_CLIENT_ID"]
        client_secret = arms["ARM_CLIENT_SECRET"]
        tenant_id = arms["ARM_TENANT_ID"]
        
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id
        }
    
    @classmethod
    def load_env(cls, env: str, proj_dir: Path):
        config_file: Path = Path(proj_dir)
        
        config_file /= f".env.{env}" # this will dynamically look for the environment based on the `env` supplied
        
        use_arm_env = os.getenv('ARM_VARS_USE_EXISTING')
        
        if not use_arm_env:
            if config_file == Path(proj_dir):
                raise FileNotFoundError("config not set properly: %s" % config_file)
            config = cls(fpath=str(config_file.absolute()))
        else:
            config = cls(fpath=None)
        
        config.read_and_parse()
        return config
