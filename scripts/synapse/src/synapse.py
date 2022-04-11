from src import _AzureResource
from typing import Any


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


class SynResource(_AzureResource):
    """
    Object class representing Synapse JSON resource
    """

    def __init__(self, jdata: dict):
        name = jdata['name']
        properties = jdata['properties']
        super().__init__(name, properties)


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
        super().__init__(jdata)
        self.activities = list()
        self._jdata = jdata

        for actJdata in jdata['properties']['activities']:
            self.activities.append(self.PipelineActivity(actJdata))

    def __eq__(self, other):
        return self._jdata == other._jdata

    def __neq__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<%s/Activities: %s>" % (self.name,
                                        str([(x.name, x.type)
                                             for x in self.activities]))
