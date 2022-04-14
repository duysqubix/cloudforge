from pathlib import Path

import json

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
    armt = SynArmTemplate(workspace_name="ec360-syn-main-dev")

    for rtype in valid_resources:
        for jfile in (mainDir / rtype).glob("*.json"):
            print("Processing..", jfile)
            with open(jfile, 'r') as f:
                jdata = json.load(f)

                cls = eval("Syn" + (rtype[0].upper() + rtype[1:]))
                res = cls(jdata)

                res.populate_dependencies()

                armr = res.convert_to_arm(res)
                armt.add_resource(armr)

    with open("exampleARM.json", 'w') as f:
        json.dump(armt.to_arm_json(), f, indent=2)
        #json.dump(armt.to_arm_json(), f, indent=2))
