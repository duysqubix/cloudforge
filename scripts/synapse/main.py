from pathlib import Path

import json

from src.synapse import SynPipeline
from src.arm import SynArmTemplate
import sys

sys.setrecursionlimit(100)
if __name__ == '__main__':
    pipelines_dir = Path(
        __file__).parent / ".syntest/ec360-syn-main-dev/pipeline/"

    arm_template = SynArmTemplate(workspace_name="ec360-syn-main-dev")

    for file in pipelines_dir.glob("*.json"):
        if not ("Truncate" in file.name):
            continue
        synPipelineJson = json.loads(file.read_bytes())
        res = SynPipeline(synPipelineJson)
        res.populate_dependencies()
        print(res.deptracker)
        x = res.convert_to_arm(res)
        arm_template.add_resource(x)
        print(json.dumps(arm_template.to_arm_json(), indent=2))
        break
