from src import RESOURCE_MAP, AzResource, AzDependency
from src.arm import ArmResource, ArmTemplate, ArmSynPipeline, ArmSynLinkedService
from typing import Any, List, Optional


class SynManager:
    __err_invalid_instance = "Invalid instance, expected {}, got {}"

    def __init__(self):
        self.resources: dict = {SynPipeline: []}

    # self.credential = list()
    # self.dataset = list()
    # self.integrationRuntime = list()
    # self.linkedService = list()
    # self.pipeline: List[SynPipeline] = list()
    # self.trigger = list()

    def _validate_instance(self, obj, cls):
        if not isinstance(obj, cls):
            raise ValueError(self.__err_invalid_instance.format(
                cls, type(obj)))

    def _add_resource(self, obj: Any, obj_type: Any):
        self._validate_instance(obj, obj_type)
        self.resources[obj_type].append(obj)

    def add_pipeline(self, pipeline):
        self._add_resource(pipeline, SynPipeline)

    def convert_to_arm_objs(self) -> ArmTemplate:
        "converts all internal objects to a valid ArmTemplate Object"
        return ArmTemplate()


class SyntoArmModule:
    """Helper class that contains logic for converting a SynResource into a SynArm
    Resource
    """

    class ConversionError(Exception):
        pass

    def __init__(self):
        super().__init__()

    def convert_to_arm(self, resource) -> ArmResource:
        if not issubclass(type(resource), SynResource):
            raise ValueError("resource object is not a subclass of %s" %
                             type(resource))
        type_name = str(type(resource))

        if "SynResource" in type_name:
            raise ValueError("resourceource object shouldn't use BaseClass of " + \
                             "SynResource")
        for objname in RESOURCE_MAP.keys():
            if not (objname in type_name):
                continue
            armObj = eval(RESOURCE_MAP[objname])

            #################################################################
            #                                                               #
            #     Explicitly initiate object by type to handle use-cases    #
            #                                                               #
            #################################################################
            armInstance: Optional[ArmResource] = None
            if objname == 'SynPipeline':
                armInstance = armObj(name=resource.name,
                                     properties=resource.properties,
                                     workspace_name="")
            elif objname == "SynLinkedService":
                armInstance = armObj(name=resource.name,
                                     properties=resource.properties,
                                     workspace_name="")
            #################################################################
            if armInstance is None:
                raise ValueError("Resource of type: %s not implemented" %
                                 objname)
            ######## Copy Over Dependencies ########
            for dep in resource.deptracker:
                armInstance.add_dep(dep)

            return armInstance

        raise self.ConversionError("Unable to convert Syn to ARM: %s" %
                                   type_name)


class SynResource(AzResource, SyntoArmModule):
    """
    Object class representing Synapse JSON resource
    """

    def __init__(self, jdata: dict):
        name = jdata['name']
        properties = jdata['properties']

        # used to track dependencies)
        self.deptracker: List[AzDependency] = list()
        super().__init__(name, properties)

    def populate_dependencies(self, data=None):
        """
        Identifies dependencies on on a resource
        """
        if data is None:
            self.deptracker.clear()
            data = self.properties

        if isinstance(data, dict):
            if "type" in data.keys() and "referenceName" in data.keys():
                type_ = data["type"]
                name = data["referenceName"]

                dep = AzDependency(name, type_)

                # if any dep already exists.. return this recursive step
                if any([(x == dep) for x in self.deptracker]):
                    return
                self.deptracker.append(dep)
            else:
                for _, v in data.items():
                    self.populate_dependencies(v)

        elif isinstance(data, list):
            for elem in data:
                self.populate_dependencies(elem)
        else:
            return


class SynLinkedService(SynResource):
    """
    Object representing a synapse linkedService resource
    """
    pass


class SynPipeline(SynResource):
    """
    Object representing a synapse pipeline resource
    """

    class PipelineActivity:

        def __init__(self, jdata: dict):
            self.type = jdata['name']
            self.name = jdata['type']
            self._jdata = jdata

        def __eq__(self, other):
            return self._jdata == other._jdata

        def __neq__(self, other):
            return not self.__eq__(other)

    def __init__(self, jdata: dict):
        self.activities = list()
        self._jdata = jdata

        for actJdata in jdata['properties']['activities']:
            self.activities.append(self.PipelineActivity(actJdata))

        super().__init__(jdata)

    def __eq__(self, other):
        return self._jdata == other._jdata

    def __neq__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<%s/Activities: %s>" % (self.name,
                                        str([(x.name, x.type)
                                             for x in self.activities]))
