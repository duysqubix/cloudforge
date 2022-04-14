from pathlib import Path

import json

from src.synapse import *
from src.arm import SynArmTemplate
import sys

sys.setrecursionlimit(500)
if __name__ == '__main__':

    valid_resources = [
        #"pipeline",
        #"likedService",
        #"credential",
        #"trigger",
        #"dataset",
        "notebook"
    ]

    mainDir = Path(__file__).parent / ".syntest/ec360-syn-main-dev/"
    armt = SynArmTemplate(workspace_name="ec360-syn-main-dev")

    for rtype in valid_resources:
        for jfile in (mainDir / rtype).glob("*.json"):
            with open(jfile, 'r') as f:
                jdata = json.load(f)

                cls = eval("Syn" + rtype.capitalize())
                res = cls(jdata)

                res.populate_dependencies()

                armr = res.convert_to_arm(res)
                armt.add_resource(armr)
    print(json.dumps(armt.to_arm_json(), indent=2))
