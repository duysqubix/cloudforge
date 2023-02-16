"""
ec tf action env
ec syn arm --options
ec syn prettify --options

"""
from argparse import ArgumentParser, Namespace
from pathlib import Path

from . import TMP_PATH
from .tokenizer import Tokenizer
from .terraform import TerraformBinWrapper


class TerraformCommands:
    def __init__(self, args: Namespace) -> None:
        self.targeted_action = args.action
        self.tf = TerraformBinWrapper(args.env)
        self.args = args
    
    def _init_terraform(self):
        tokenizer = Tokenizer(self.args.proj_dir, "tf")
        tokenizer.read_root()
        
        config = self.tf.get_config(self.args.proj_dir)
        
        arms = config.get_arms()
        client_id = arms["ARM_CLIENT_ID"]
        client_secret = arms["ARM_CLIENT_SECRET"]
        tenant_id = arms["ARM_TENANT_ID"]
        vault_name = config.get("KEY_VAULT_NAME")
        
        # get secrets from Key Vault
        tokens = {"STORAGENAME": "yes", "LOCATION": "HERE"}
        parsed_tree = tokenizer.replace_and_validate_tokens(tokens)
        
        tokenizer.dump_to(tree=parsed_tree, dirpath=TMP_PATH, unique=True)
        
    
    def execute(self):
        self._init_terraform()

class ECArgParser(ArgumentParser):
    
    def init(self):
        cwd = Path.cwd()
        sub_parser = self.add_subparsers(help='Available subcommands', dest='subcmd')

        tf_subcmd = sub_parser.add_parser('tf', help='Terraform available commands', prefix_chars='tf-')
        tf_subcmd.add_argument("action", choices=['validate', 'deploy', 'debug'], help="Choose an action")
        tf_subcmd.add_argument("env", choices=['dev', 'stg', 'uat', 'prod'], help="Choose an targeted environment")
        tf_subcmd.add_argument("-d", "--proj-dir", default=str(cwd.absolute()), type=lambda x: Path(x))
        return self.parse_args()

def execute():
    parser = ECArgParser(prog='ec')
    args = parser.init()
    if args.subcmd == 'tf':
        tfcmds = TerraformCommands(args)
        tfcmds.execute()