"""
Handles the deployment piece by reading a static deployment file
and modifiying attributes based on dot notation searching in JSON files
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from functools import reduce

from . import logger

import json


def pretty_print_modified_actions(result):
    for rtype, mods in result.items():
        logger.debug(rtype.upper())
        for mod in mods:
            logger.debug(mod["name"])
            logger.debug(json.dumps(mod, indent=4))
            logger.debug("*" * 50)


class InvalidDotNotation(Exception):
    pass


class MissingParameterError(Exception):
    pass


class NotValidActionError(Exception):
    pass


class Action:
    """
    Represents a single action to perform
    """

    def __init__(self, name: str, path: str, value: str, action: str):
        self.name = name
        self.path = path
        self.value = value
        self.action = action

    @classmethod
    def from_dict(cls, d) -> Action:
        name = d.get("name")
        path = d.get("path")
        value = d.get("value")
        action = d.get("action")

        for attr in (name, path, value, action):
            if attr is not None:
                continue

            raise MissingParameterError("Missing parameter: %s" % attr)

        return cls(name, path, value, action)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __neq__(self, other):
        return not self.__eq__(other)


class ActionTemplate:
    pass





class ActionExecutioner:
    """
    Manages the execution of actions on arbitrary valid json
    """

    __valid_actions = ("update",)

    def __init__(self):
        self.target: Optional[Dict[Any, Any]] = None  # buffer to hold final dictionary

    def _parse_dot_notation(self, dot_str: str) -> List[str]:
        tokens: List[str] = list(map(str, dot_str.split(".")))

        if tokens[0] != "$":
            raise InvalidDotNotation("Expecting '$' as root")
        return tokens[1:]

    def _get_item(self, item: Any, x: Any):
        if str(x).isnumeric():
            x = int(x)
        return item.__getitem__(x)

    def _get_by_path(self, root: Dict[str, str], items: List[str]):
        return reduce(self._get_item, items, root)

    def _set_by_path(self, root: Dict[str, str], items: List[str], value: str):
        self._get_by_path(root, items[:-1])[items[-1]] = value

    def get_by_dot_notation(self, dot_str: str, target: Dict[Any, Any]) -> str:
        tokens = self._parse_dot_notation(dot_str)
        return self._get_by_path(target, tokens)

    def update_by_dot_notation(
        self, dot_str: str, new_value: str, target: Dict[Any, Any]
    ) -> Dict[Any, Any]:
        tokens = self._parse_dot_notation(dot_str)
        self._set_by_path(target, tokens, new_value)
        return target

    def _do_action_update(self, action: Action, jdata):
        self.update_by_dot_notation(action.path, action.value, jdata)

    def _do_action(self, action: Action, jdata: dict):
        if not self.target:
            self.target = jdata

        if action.action == "update":
            self._do_action_update(action, self.target)

    def execute(self, action: Action, jdata: Dict[Any, Any]):
        if action.action not in self.__valid_actions:
            raise NotValidActionError()
        self._do_action(action, jdata)
