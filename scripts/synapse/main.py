from pathlib import Path

import json

from src.synapse import SynLinkedService, SynPipeline
from src.arm import SynArmTemplate
import sys

sys.setrecursionlimit(100)
if __name__ == '__main__':
    #    pipelines_dir = Path(
    #        __file__).parent / ".syntest/ec360-syn-main-dev/pipeline/"
    #
    #    arm_template = SynArmTemplate(workspace_name="ec360-syn-main-dev")
    #
    #    for file in pipelines_dir.glob("*.json"):
    #        if not ("Truncate" in file.name):
    #            continue
    #        synPipelineJson = json.loads(file.read_bytes())
    #        res = SynPipeline(synPipelineJson)
    #        res.populate_dependencies()
    #        x = res.convert_to_arm(res)
    #        arm_template.add_resource(x)
    #        print(json.dumps(arm_template.to_arm_json(), indent=2))
    #        break

    pipelineDir = Path(
        __file__).parent / ".syntest/ec360-syn-main-dev/pipeline"

    linkedServiceDir = Path(
        __file__).parent / ".syntest/ec360-syn-main-dev/linkedService"

    pipelineF = [x for x in pipelineDir.glob("*.json")][0]
    lksF = [x for x in linkedServiceDir.glob("*.json")][0]

    pipelineJson, lksJson = None, None

    with open(pipelineF, 'r') as pip, open(lksF, 'r') as lksf:
        pipelineJson = json.load(pip)
        lksJson = json.load(lksf)

    armt = SynArmTemplate(workspace_name="ec360-syn-main-dev")

    pipeline_resource = SynPipeline(pipelineJson)
    lks_resource = SynLinkedService(lksJson)

    for res in [pipeline_resource, lks_resource]:
        res.populate_dependencies()
        armr = res.convert_to_arm(res)

        armt.add_resource(armr)
    print(json.dumps(armt.to_arm_json(), indent=2))
