from typing import List, Optional
from typing import Any, Dict, List, Optional

from . import (
    RESOURCE_MAP,
    SYN_RESOURCE_TO_OBJ,
    VALID_CELL_MAGIC_COMMANDS,
    AzResource,
    AzDependency,
    VALID_LINE_MAGIC_COMMANDS,
    logger,
)

from .arm import *
from .jsonr import ActionTemplate, Action, ActionExecutioner

import pyjson5 as json5

class SynapseActionTemplate(ActionTemplate):
    """
    A compilation of actions based on resource type
    """

    def __init__(self, config_data: Dict[str, List[Dict[str, str]]]):
        self._map: Dict[str, List[Action]] = {
            "linkedService": [],
            "trigger": [],
            "integrationRuntime": [],
            "dataset": [],
            "credential": [],
            "notebook": [],
            "pipeline": [],
        }

        for rtype in self._map.keys():
            config_resource: Optional[List[Dict[str, str]]] = config_data.get(
                str(rtype)
            )

            if not config_resource:
                continue

            action_objs = []

            for rjson in config_resource:
                act_obj = Action.from_dict(rjson)
                action_objs.append(act_obj)

            self._map[rtype].extend(action_objs)

    def process_synapse_workspace(
        self, wkspace_root: str, inplace=False
    ) -> Dict[Any, Any]:
        changes = {}

        for rtype, actions in self._map.items():
            resource_dir = wkspace_root + "/" + rtype + "/"

            changes[rtype] = []

            for action in actions:
                filename = resource_dir + action.name + ".json"
                with open(filename, "r+") as f:
                    target = json5.load(f)

                    ae = ActionExecutioner()
                    ae.execute(action, target)

                    changes[rtype].append(ae.target)

                if inplace:
                    with open(filename, "w") as f:
                        modifiedTarget = ae.target
                        json5.dump(modifiedTarget, f)

        return changes

    def __eq__(self, other):
        return self._map == other._map

    def __neq__(self, other):
        return not self.__eq__(other)


class SynManager:
    def __init__(self, workspace_name):
        self.workspace_name = workspace_name
        self.resources = {k: [] for k in SYN_RESOURCE_TO_OBJ.keys()}

    def add_resource(self, rtype: str, jdata: dict):
        cls = eval(SYN_RESOURCE_TO_OBJ[rtype])

        obj = cls(jdata)
        obj.populate_dependencies()
        self.resources[rtype].append(obj)

    def convert_to_arm_objs(self) -> ArmTemplate:
        armt = SynArmTemplate(workspace_name=self.workspace_name)
        for rtype, res_lst in self.resources.items():
            print(f"Converting.......{rtype}")
            for res in res_lst:
                res.populate_dependencies()
                armr = res.convert_to_arm(res)
                armt.add_resource(armr)
        return armt


class SyntoArmModule:
    """Helper class that contains logic for converting a SynResource into a SynArm
    Resource
    """

    class ConversionError(Exception):
        pass

    def convert_to_arm(self, resource) -> ArmResource:
        if not issubclass(type(resource), SynResource):
            raise ValueError("resource object is not a subclass of %s" % type(resource))
        type_name = str(type(resource))

        if "SynResource" in type_name:
            raise ValueError(
                "resourceource object shouldn't use BaseClass of " + "SynResource"
            )
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
            if objname == "SynPipeline":
                armInstance = armObj(
                    name=resource.name,
                    properties=resource.properties,
                    workspace_name="",
                )
            elif objname == "SynLinkedService":
                armInstance = armObj(
                    name=resource.name,
                    properties=resource.properties,
                    workspace_name="",
                )

            elif objname == "SynTrigger":
                armInstance = armObj(
                    name=resource.name,
                    properties=resource.properties,
                    workspace_name="",
                )
            elif objname == "SynCredential":
                armInstance = armObj(
                    name=resource.name,
                    properties=resource.properties,
                    workspace_name="",
                )

            elif objname == "SynDataset":
                armInstance = armObj(
                    name=resource.name,
                    properties=resource.properties,
                    workspace_name="",
                )
            elif objname == "SynNotebook":
                # preformat code
                # resource.format_code()

                armInstance = armObj(
                    name=resource.name,
                    properties=resource.properties,
                    workspace_name="",
                )

            elif objname == "SynIntegrationRuntime":
                armInstance = armObj(
                    name=resource.name,
                    properties=resource.properties,
                    workspace_name="",
                )

            #################################################################
            if armInstance is None:
                raise ValueError("Resource of type: %s not implemented" % objname)
            ######## Copy Over Dependencies ########
            for dep in resource.deptracker:
                armInstance.add_dep(dep)

            return armInstance

        raise self.ConversionError("Unable to convert Syn to ARM: %s" % type_name)


class SynResource(AzResource, SyntoArmModule):
    """
    Object class representing Synapse JSON resource
    """

    def __init__(self, jdata: dict):
        name = jdata["name"]
        properties = jdata["properties"]

        # used to track dependencies)
        self.deptracker: List[AzDependency] = list()
        super().__init__(name, properties)

        self._ctn = 0

    def populate_dependencies(self):
        self.deptracker.clear()
        return self._populate_dependencies(data=self.properties)

    def _populate_dependencies(self, data):
        """
        Identifies dependencies on on a resource
        """
        if isinstance(data, dict):
            if "type" in data.keys() and "referenceName" in data.keys():
                type_ = data["type"]
                name = data["referenceName"]

                ignore = False

                if any([x in type_.lower() for x in ("sqlpool", "bigdatapool")]):
                    ignore = True

                # ignore WorkSpaceDefault Dependencies
                if "WorkspaceDefault" in name:
                    print("Name AND TYPE: ", name, type)
                    ignore = True

                dep = AzDependency(name, type_, ignore=ignore)

                # if any dep already exists.. return this recursive step
                if any([(x == dep) for x in self.deptracker]):
                    return
                self.deptracker.append(dep)
            else:
                for _, v in data.items():
                    self._populate_dependencies(v)

        elif isinstance(data, list):
            for elem in data:
                self._populate_dependencies(elem)
        else:
            return


class SynNotebook(SynResource):
    """
    Object representing a spark notebook resource
    """

    def init(self):
        try:
            self.default_language = self.properties["metadata"]["language_info"]["name"]
        except KeyError:
            self.default_language = "python"

    def _magic_command_in_line(self, code_str):
        return any([x in code_str for x in VALID_LINE_MAGIC_COMMANDS])

    def _magic_command_cell(self, code_str):
        return any([x in code_str for x in VALID_CELL_MAGIC_COMMANDS])

    def _code_list_to_str(self, code: List[str], ignore_magic=False) -> str:
        code_lst = code[:]

        for idx in range(len(code_lst)):
            line = code_lst[idx]
            line = line.replace("\n\r", "\n")

            logging.debug(
                "MAGIC_IN_LINE: ",
                self._magic_command_in_line(line),
                " | IGNORE_MAGIC: ",
                ignore_magic,
            )
            if self._magic_command_in_line(line) and (not ignore_magic):
                line = "# " + line
                logging.debug("ADD_COMMENT: ", line)
                code_lst[idx] = line
        return "".join(code_lst)

    def _code_str_to_list(self, code: str) -> List[str]:
        lst = []
        for line in code.split("\n"):
            if line != "":
                line = line.rstrip() + "\r\n"
                logging.debug("LINE: ", repr(line))
                lst.append(line)
        return lst

    def format_code(self):
        for idx, cell in enumerate(self.properties["cells"]):
            logging.debug("IDX: ", idx, cell["source"])
            code_str = self._code_list_to_str(cell["source"], ignore_magic=False)

            logging.debug("CODE: ", repr(code_str))
            # checks to see if cell code is written not in default_language
            # precense of magic cell block indicates this
            if not self._magic_command_cell(code_str):
                code_fmt = ""

                if self.default_language == "python":
                    code_fmt = self._format_python_code(code_str)

                else:
                    logging.warning(
                        "language not supported formatting: %s" % self.default_language
                    )

                code_fmt_lst = self._code_str_to_list(code_fmt)
                self.properties["cells"][idx]["source"] = code_fmt_lst

    def _format_python_code(self, code: str) -> str:
        logging.debug("PREFORMAT", repr(code))
        code = code.replace("\xa0", " ")
        fmt_code, _ = FormatCode(code)

        # uncomment magic line commands
        final_lst = []
        for line in self._code_str_to_list(fmt_code):
            if self._magic_command_in_line(line):
                logging.debug("PRE_MAGIC_REMOVE: ", repr(line))
                line = line[2:]
                logging.debug("POST_MAGIC_REMOVE: ", repr(line))
            final_lst.append(line)

        final_code = self._code_list_to_str(final_lst, ignore_magic=True)
        logging.debug("POSTFORMAT: ", repr(final_code))
        return final_code


class SynIntegrationRuntime(SynResource):
    """
    Object representing a synapose Integration Runtime resource
    """


class SynDataset(SynResource):
    """
    Object representing a synapse Dataset resource
    """


class SynCredential(SynResource):
    """
    Object representing a synapse Credential resource
    """


class SynTrigger(SynResource):
    """
    Object representing a synapse trigger resource
    """


class SynLinkedService(SynResource):
    """
    Object representing a synapse linkedService resource
    """


class SynPipeline(SynResource):
    """
    Object representing a synapse pipeline resource
    """

    class PipelineActivity:
        def __init__(self, jdata: dict):
            self.type = jdata["name"]
            self.name = jdata["type"]
            self._jdata = jdata

        def __eq__(self, other):
            return self._jdata == other._jdata

        def __neq__(self, other):
            return not self.__eq__(other)

    def __init__(self, jdata: dict):
        self.activities = list()
        self._jdata = jdata

        for actJdata in jdata["properties"]["activities"]:
            self.activities.append(self.PipelineActivity(actJdata))

        super().__init__(jdata)

    def __eq__(self, other):
        return self._jdata == other._jdata

    def __neq__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<%s/Activities: %s>" % (
            self.name,
            str([(x.name, x.type) for x in self.activities]),
        )
