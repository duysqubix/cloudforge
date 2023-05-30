"""
json_config_processor.py

This module provides the JSONConfigProcessor functionality to process JSON files
based on a configuration that defines a set of actions, such as updating, inserting,
removing, or adding elements. The module contains two main classes, Action and Configuration,
which represent individual actions and a collection of actions for a specific key, respectively.

Usage Example:

1. Create a Configuration JSON string:

    config_json = '''
    {
        "linkedService": [
            {
                "name": "LKS_AKV_SecretStore",
                "path": "$.properties.typeProperties.baseUrl",
                "action": "update",
                "value": "https://new_url"
            }
        ]
    }
    '''

2. Load the configuration:

    from json_config_processor import Configuration
    config = Configuration(config_json)

3. Execute actions on JSON files:

    directory_path = "path/to/json/files"
    modified_files = config.execute_actions("linkedService", directory_path)

4. Access the updated JSON data:

    updated_data = modified_files["path/to/json/files/LKS_AKV_SecretStore.json"]
    new_base_url = updated_data["properties"]["typeProperties"]["baseUrl"]

The module enables users to define and apply arbitrary actions on JSON files through an
easy-to-use and extensible interface.
"""

from pathlib import Path
from typing import Dict, Union, List
import json
import jmespath

from . import logger


class Action:
    """
    Represents an action to manipulate JSON data.

    Attributes:
        name (str): The name of the action.
        path (str): The dot-notation path to the JSON element to be manipulated.
        action (str): The type of action to perform ('update', 'insert', 'remove', 'add').
        value (str): The value to be used in the action.
    """

    def __init__(self, action_data: Dict[str, Union[str, List[str]]]) -> None:
        self.name = action_data["name"]
        self.path = action_data["path"]
        self.action = action_data["action"]
        self.value = action_data["value"]

        if not self.path.startswith("$."):
            logger.critical("Path in Action must start with '$.'")

        self.path = self.path[2:]  # Remove the '$.' from the path

    def validate_path(self, json_data: Dict[str, Union[str, List[str]]]) -> bool:
        """
        Validates if the provided JSON dot-notation path is valid for the given JSON data.

        Args:
            json_data (Dict[str, Union[str, List[str]]]): The JSON data to be validated.

        Returns:
            bool: True if the path is valid, False otherwise.
        """
        try:
            jmespath.search(self.path, json_data)
            return True
        except jmespath.exceptions.ParseError:
            return False

    def execute(
        self, json_data: Dict[str, Union[str, List[str]]]
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Executes the action on the given JSON data.

        Args:
            json_data (Dict[str, Union[str, List[str]]]): The JSON data to be manipulated.

        Returns:
            Dict[str, Union[str, List[str]]]: The manipulated JSON data.
        """

        if not self.validate_path(json_data):
            logger.error(
                f"Path, `{self.path}`, does not exist for action `{self.name}`."
            )

        if self.action == "update":
            json_data = self.update(json_data)
        elif self.action == "insert":
            json_data = self.insert(json_data)
        elif self.action == "remove":
            json_data = self.remove(json_data)
        elif self.action == "add":
            json_data = self.add(json_data)

        return json_data

    def update(self, json_data):
        if "." in self.path:
            parent_path, last_key = self.path.rsplit(".", 1)
            parent_element = jmespath.search(parent_path, json_data)
        else:
            last_key = self.path
            parent_element = json_data

        parent_element[last_key] = self.value
        return json_data

    def insert(self, json_data):
        # To be implemented based on specific requirements
        pass

    def remove(self, json_data):
        # To be implemented based on specific requirements
        pass

    def add(self, json_data):
        # To be implemented based on specific requirements
        pass


class Configuration:
    """
    Represents a configuration to execute a series of actions on JSON files.

    Attributes:
        config_data (Dict): The JSON data from the configuration file.
        actions_map (Dict[str, List[Action]]): A mapping of action categories to lists of Action objects.
    """

    def parse_actions(self):
        raise NotImplementedError

    def execute_actions(self, key: str, directory_path: str) -> Dict[str, Dict]:
        raise NotImplementedError


class SynapseWorkspaceConfiguration(Configuration):
    def __init__(self, config_json: str) -> None:
        self.config_data = json.loads(config_json)
        self.actions_map: Dict[str, List[Action]] = {
            "linkedService": [],
            "dataset": [],
            "trigger": [],
            "integrationRuntime": [],
            "pipeline": [],
            "sqlscript": [],
        }
        self.parse_actions()

    def parse_actions(self) -> None:
        """
        Parses the config_data and creates Action objects for all actions.
        """
        for key, actions in self.config_data.items():
            if key in self.actions_map:
                self.actions_map[key] = [Action(action_data) for action_data in actions]

    def execute_actions(self, key: str, directory_path: str) -> Dict[str, Dict]:
        """
        Executes the actions on the corresponding JSON files in the specified directory.

        Args:
            key (str): The action category (e.g., 'linkedService', 'dataset').
            directory_path (str): The path to the directory containing the JSON files.
        """
        modified = {}
        if key in self.actions_map:
            actions = self.actions_map[key]

            for action in actions:
                name = action.name
                file_path = Path(directory_path) / f"{name}.json"

                if file_path.exists():
                    with file_path.open("r") as f:
                        json_data = json.load(f)
                        json_data = action.execute(json_data)

                        modified[str(file_path.absolute())] = json_data
                else:
                    print(f"File {file_path} not found.")
        return modified
