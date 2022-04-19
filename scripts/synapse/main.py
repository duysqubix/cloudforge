from pathlib import Path

import json

from src import SYN_RESOURCE_TO_OBJ
from src.synapse import *
from src.arm import SynArmTemplate
import sys

sys.setrecursionlimit(500)
if __name__ == '__main__':

    valid_resources = [
        "pipeline", "linkedService", "credential", "trigger", "dataset",
        "notebook", "integrationRuntime"
    ]

    mainDir = Path(__file__).parent / ".syntest/"
    synm = SynManager(workspace_name="ec360-syn-main-dev")

    for rtype in valid_resources:
        for jfile in (mainDir / rtype).glob("*.json"):
            with open(jfile, 'r') as f:
                jdata = json.load(f)

                synm.add_resource(rtype, jdata)
    armt = synm.convert_to_arm_objs()

    with open("exampleARM.json", 'w') as f:
        json.dump(armt.to_arm_json(), f, indent=2)
        #json.dump(armt.to_arm_json(), f, indent=2))
