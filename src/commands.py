"""
ec tf action env
ec syn arm --options
ec syn prettify --options

"""
from argparse import ArgumentParser, Namespace
from pathlib import Path
from azure.identity import ClientSecretCredential


from . import TMP_PATH, logger
from .tokenizer import Tokenizer
from .terraform import TerraformBinWrapper
from .keyvault import AzureKeyVault
from .utils import EnvConfiguration


class BaseCommand:
    def __init__(self, args: Namespace) -> None:
        self._args = args            
        self.setup()
    
    def setup(self):
        pass

class TerraformCommands(BaseCommand):
    def setup(self) -> None:
        self.targeted_action = self._args.action
        self.tf = TerraformBinWrapper(self._args.env)
        
        tokenizer = Tokenizer(self._args.proj_dir, "tf")
        tokenizer.read_root()
        
        self.config = EnvConfiguration.load_env(self.tf.env, self._args.proj_dir)
        

        vault_name = self.config.get("KEY_VAULT_NAME")
        
        auth = ClientSecretCredential(**self.config.get_terraform_creds())
        tokens = AzureKeyVault(vault_name, auth).get_secrets()
        
        # get secrets from Key Vault
        parsed_tree = tokenizer.replace_and_validate_tokens(tokens)
        
        tokenizer.dump_to(tree=parsed_tree, dirpath=TMP_PATH, unique=True)
        
    
    def execute(self):
        pass

class ECArgParser(ArgumentParser):
    
    def init(self):
        self.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
        cwd = Path.cwd()
        sub_parser = self.add_subparsers(help='Available subcommands', dest='subcmd')

        tf_subcmd = sub_parser.add_parser('tf', help='Terraform available commands', prefix_chars='tf-')
        tf_subcmd.add_argument("action", choices=['validate', 'deploy', 'debug'], help="Choose an action")
        tf_subcmd.add_argument("env", choices=['dev', 'stg', 'uat', 'prod'], help="Choose an targeted environment")
        tf_subcmd.add_argument("-d", "--proj-dir", default=str(cwd.absolute()), type=lambda x: Path(x), help=f"Define the project directory that holds ECTF files. Default: {str(cwd.absolute())}")
        return self.parse_args()

def execute():
    parser = ECArgParser(prog='ec')    
    args = parser.init()
    
    if args.verbose:
        logger.enable_debug()
        logger.enable_file_logging()
    
    if not args:
        parser.print_help()
        return

    if args.subcmd == 'tf':
        tfcmds = TerraformCommands(args)
        tfcmds.execute()
    else:
        parser.print_help()
    
    logger.disable_debug()
    logger.disable_file_logging()
