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
parser.add_argument("--dry-run",
                    help="Performs a dry run of program",
                    action="store_true")

parser.add_argument("--debug",
                    help="outputs debug information",
                    action="store_true")

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

    replace = True

    if args.dry_run is True:
        replace = False

    result = syn_action_template.process_synapse_workspace(
        str(syn_workspace_dir), inplace=replace)

    if args.debug is True:
        pretty_print_modified_actions(result)
