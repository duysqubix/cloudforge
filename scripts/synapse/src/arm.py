from __init__ import _AzureResource
from typing import List


class ArmParameter:
    pass


class ArmTemplate():

    def __init__(self):
        self.resources: List[ArmResource] = list()
        self.parameters: List[ArmParameter] = list()
        self.schema = "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
        self.contentVersion = "1.0.0.0"


class ArmResource(_AzureResource):
    """
    Object class representing ARM JSON Resource
    """

    def __init__(self, name, properties):
        super().__init__(name, properties)
        # list of resources by workspaceId
        # ex: Microsoft.Synapse/workspaces/{WORKSPACE_NAME]/[RESOURCE_TYPE/[RESOURCE_NAME]
        self.dependsOn: List[str] = list()
