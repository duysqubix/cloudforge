from typing import List
from src import ARM_SCHEMA, ARM_VERSION, AzDependency, AzResource


class ArmTemplate:
    __workspaceId__ = ""

    @property
    def workspaceId(self):
        if not self.__workspaceId__:
            raise NotImplementedError("Base class not meant to be initiated")

        return self.__workspaceId__


class ArmResource(AzResource):
    """
    Object class representing ARM JSON Resource
    """
    __resource_type__ = "_INVALID_"

    def __init__(
        self,
        name: str,
        properties: dict,
        workspace_name: str = "",
    ):

        self.workspace_name = workspace_name
        self.depends_on: List[AzDependency] = []
        self.api_version = ARM_VERSION
        self.type = ""
        super().__init__(name, properties)

    def add_dep(self, *deps: AzDependency):
        for dep in deps:
            if not isinstance(dep, AzDependency):
                raise ValueError("Dependency not of correct instance %s/%s",
                                 type(dep), dep)

            self.depends_on.append(dep)

    def get_dependencies(self, prefix="") -> List[str]:
        """formats dependencies"""
        return [dep.formatARM(prefix=prefix) for dep in self.depends_on]

    def to_arm_json(self, prefix="") -> dict:
        return {
            "name": self.workspace_name + "/" + self.name,
            "type": self.workspace_id,
            "apiVersion": self.api_version,
            "properties": self.properties,
            "dependsOn": self.get_dependencies(prefix=prefix)
        }

    def __eq__(self, other):
        return (self.type == other.type
                and all([x in other.depends_on
                         for x in self.depends_on]) and self.name == other.name
                and self.properties == other.properties)

    def __neq__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<%s/%s>" % (self.name, len(self.depends_on))

    @property
    def workspace_id(self):
        return self.type + "/" + self.__resource_type__


class ArmSynResource(ArmResource):

    def init(self):
        self.type = "Microsoft.Synapse/workspaces"


class ArmSynTrigger(ArmSynResource):
    """
    Object class representing an ARM Synapse Trigger Resource
    """

    __resource_type__ = "triggers"


class ArmSynLinkedService(ArmSynResource):
    """
    Object class representing an ARM Synapse Linked Service Resource
    """
    __resource_type__ = "linkedServices"


class ArmSynPipeline(ArmSynResource):
    """
    Object class representing a ARM Pipeline Resource
    """
    __resource_type__ = "pipelines"


class SynArmTemplate(ArmTemplate):
    """
    Object class that reprents a serialized abstraction of the ArmTemplate file
    for Synapse
    """
    __workspaceId__ = "Microsoft.Synapse/workspaces"

    def __init__(self, workspace_name: str):
        self.workspace_name = workspace_name
        self._resources: List[ArmResource] = list()
        self._schema = ARM_SCHEMA

        self._content_version = "1.0.0.0"

    def add_resource(self, resource: ArmResource):

        if not isinstance(resource, ArmResource):
            raise ValueError(
                "Can only add ArmResource [and children] to collection")
        resource.workspace_name = self.workspace_name
        self._resources.append(resource)

    def to_arm_json(self):
        depends_on = []
        for resource in self._resources:
            prefix = self.workspaceId + "/" + self.workspace_name
            depends_on_str = resource.to_arm_json(prefix=prefix)
            depends_on.append(depends_on_str)

        return {
            "$schema": self._schema,
            "contentVersion": self._content_version,
            "resources": depends_on
        }
