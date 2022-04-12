from typing import List
from src import AzResource


class ArmParameter:
    pass


class ArmTemplate:
    __workspaceId__ = ""

    @property
    def workspaceId(self):
        if not self.__workspaceId__:
            raise NotImplementedError("Base class not meant to be initiated")

        return self.__workspaceId__


class SynArmTemplate():
    _workspace_id = "Microsoft.Synapse/workspaces"

    def __init__(self, workspace_name: str):
        self.resources: List[ArmResource] = list()
        self.parameters: List[ArmParameter] = list()
        self.schema = "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
        self.content_version = "1.0.0.0"


class ArmResource(AzResource):
    """
    Object class representing ARM JSON Resource
    """

    def __init__(self, name, properties):
        super().__init__(name, properties)
        # list of resources by workspaceId
        # ex: Microsoft.Synapse/workspaces/{WORKSPACE_NAME]/[RESOURCE_TYPE/[RESOURCE_NAME]
        self.depends_on: List[str] = list()
