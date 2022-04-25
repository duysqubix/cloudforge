from pathlib import Path

import argparse
import json

from src.synapse import *
from src.jsonr import ActionExecutioner, ActionTemplate, SynapseActionTemplate, pretty_print_modified_actions

parser = argparse.ArgumentParser()
parser.add_argument("--dir", help="Path to synapse workspace", required=True)
parser.add_argument("--config",
                    help="Path to deployment configuration file",
                    required=True)

if __name__ == '__main__':
    args = parser.parse_args()

    syn_workspace_dir = Path(args.dir)
    config_file = Path(args.config)

    if not syn_workspace_dir.is_dir():
        raise FileNotFoundError("Synapse Workspace not a valid directory")

    if not config_file.is_file():
        raise FileNotFoundError(
            "Deployment configuration file not valid or missing")

    config = json.load(open(config_file))
    syn_action_template = SynapseActionTemplate(config)

    result = syn_action_template.process_synapse_workspace(
        str(syn_workspace_dir))
    pretty_print_modified_actions(result)
#    valid_resources = [
#        "pipeline", "linkedService", "credential", "trigger", "dataset",
#        "notebook", "integrationRuntime"
#    ]
#
#    mainDir = Path(__file__).parent / ".syntest/"
#    synm = SynManager(workspace_name="ec360-syn-main-dev")
#
#    for rtype in valid_resources:
#        for jfile in (mainDir / rtype).glob("*.json"):
#            with open(jfile, 'r') as f:
#                jdata = json.load(f)
#
#                synm.add_resource(rtype, jdata)
#    armt = synm.convert_to_arm_objs()
#
#    with open("exampleARM.json", 'w') as f:
#        json.dump(armt.to_arm_json(), f, indent=2)
#        #json.dump(armt.to_arm_json(), f, indent=2))
