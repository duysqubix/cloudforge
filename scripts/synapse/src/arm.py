from typing import List
from src import AzDependency, AzResource


class ArmTemplate:
    __workspaceId__ = ""

    def workspaceId(self):
        if not self.__workspaceId__:
            raise NotImplementedError("Base class not meant to be initiated")

        return self.__workspaceId__


class SynArmTemplate():
    _workspace_id = "Microsoft.Synapse/workspaces"

    def __init__(self, wks_name: str):
        self.wks_name = wks_name
        self.resources: List[ArmResource] = list()
        self.schema = "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
        self.content_version = "1.0.0.0"


class ArmResource(AzResource):
    """
    Object class representing ARM JSON Resource
    """

    def __init__(self, name, properties):
        super().__init__(name, properties)

        self.depends_on: List[AzDependency] = []
        self.api_version = "2019-06-01-preview"
        self.type = ""

    def add_dep(self, dep: AzDependency):
        if not isinstance(dep, AzDependency):
            raise ValueError("Dependency not of correct instance")

        self.depends_on.append(dep)


class ArmSynPipeline(ArmResource):
    """
    Object class representing a ARM Pipeline Resource
    """

    def init(self):
        self.type = "Microsoft.Synapse/workspaces/pipelines"
