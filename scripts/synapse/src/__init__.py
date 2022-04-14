class AzResource:
    """
    Base object class that represents an azure resource
    """

    def __init__(self, name: str, properties: dict):
        super().__init__()
        self.name = name
        self.properties = properties
        self.init()

    def init(self):
        pass


class AzDependency:

    def __init__(self, name, type):
        self.name = name
        self.type = type

    def formatARM(self, prefix="", suffix=""):
        t = (self.type[0].lower() + self.type[1:]).replace("Reference",
                                                           "") + "s"
        return prefix + f"/{t}/{self.name}" + suffix

    def __eq__(self, other):
        return (self.name == other.name) and \
               (self.type == other.type)

    def __neq__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.formatARM()


RESOURCE_MAP = {
    "SynPipeline": "ArmSynPipeline",
    "SynLinkedService": "ArmSynLinkedService",
    "SynTrigger": "ArmSynTrigger",
    "SynCredential": "ArmSynCredential",
    "SynDataset": "ArmSynDataset",
    "SynNotebook": "ArmSynNotebook",
    "SynIntegrationRuntime": "ArmSynIntegrationRuntime"
}

ARM_VERSION = "2019-06-01-preview"
ARM_SCHEMA = "http://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#"

#########################################################################
# last updated: April 14, 2022
#
# Source:
#   https://docs.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-development-using-notebooks
#
VALID_LINE_MAGIC_COMMANDS = [
    "%lsmagic", "%time", "%timeit", "%history", "%run", "%load"
]

VALID_CELL_MAGIC_COMMANDS = [
    "%%time", "%%timeit", "%%capture", "%%writefile", "%%sql", "%%pyspark",
    "%%spark", "%%csharp", "%%html", "%%configure"
]

VALID_MAGIC_COMMANDS = VALID_CELL_MAGIC_COMMANDS + VALID_LINE_MAGIC_COMMANDS
#########################################################################
