"""
The utils module provides the EnvConfiguration class, which represents a configuration object for environment variables.

The EnvConfiguration class provides methods to read and parse a configuration file or use environment variables, and to retrieve a dictionary of key-value pairs that have keys containing the substring "ARM_".

Example Usage:
ec = EnvConfiguration("config.env")
ec.read_and_parse()
arms = ec.get_arms()
"""

from . import logger

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
            with open(self.fpath, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    key, value = line.split("=", maxsplit=1)
                    self.key_pairs[key] = value

        if self.key_pairs.get("SAS_TOKEN"):
            self.key_pairs["SAS_TOKEN"] = self.key_pairs["SAS_TOKEN"].replace('"', "")

    def get_arms(self) -> Dict[str, str]:
        """
        Returns a dictionary of key-value pairs that have keys containing the substring "ARM_".

        Returns:
            dict: A dictionary of key-value pairs that have keys containing the substring "ARM_".
        """
        return dict(filter(lambda item: "ARM_" in item[0], self.key_pairs.items()))

    def ensure_arms_in_env(self):
        """ensure ARM_ config variables are set in environment"""
        arms = self.get_arms()

        for k, v in self.get_arms().items():
            os.environ[k] = v

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
            "tenant_id": tenant_id,
        }

    def get_azure_sp_creds(self):
        return self.get_terraform_creds()

    @classmethod
    def load_env(
        cls, env: Optional[str] = None, target_dir_or_file: Optional[Path] = None
    ) -> "EnvConfiguration":
        """
        Loads environment configuration from a file or existing environment variables.

        Args:
            env: Optional[str]: Environment name (e.g. 'prod', 'dev', 'test', etc.) used to construct the
                                configuration file name. If `target_dir_or_file` is a directory, `env`
                                must be supplied.

            target_dir_or_file: Optional[Path]:
                                Target directory or file to load the configuration from.
                                If `target_dir_or_file` is None, authentication parameters must be set in environment variables.

        Raises:
            EnvironmentError: When authentication parameters are not set in environment variables or supplied config file.
            ValueError: When `target_dir_or_file` is a directory and `env` is not supplied.
            FileNotFoundError: When the configuration file is not found.

        Returns:
            EnvConfiguration: An instance of `EnvConfiguration` class with the parsed configuration.
        """
        target = target_dir_or_file
        use_arm_env = os.getenv("ARM_VARS_USE_EXISTING")

        # Check if authentication parameters are set
        if (not use_arm_env) and (not target):
            raise EnvironmentError(
                "Authentication parameters are not set in environment variables or supplied config file"
            )
        config_file = None
        # Check if target is a file or directory
        if target:
            target = Path(target)

            if target.is_file():
                config_file = Path(target)
            else:
                # Check if env is supplied when target is a directory
                if env is None:
                    raise ValueError(
                        "target detected a directory, must supply env parameter"
                    )
                config_file = Path(target) / f".env.{env}"
            logger.debug(f"ENV: {env}, CONFIG_FILE: {config_file}")

            # Check if the configuration file exists
            if not config_file.is_file():
                raise FileNotFoundError("config file not found: %s" % config_file)

        # Load the configuration
        if not use_arm_env:
            if not config_file:
                raise EnvironmentError("ARM_USE_EXISTING not set")
            config = cls(fpath=str(config_file.absolute()))
        else:
            config = cls(fpath=None)

        config.read_and_parse()
        return config
