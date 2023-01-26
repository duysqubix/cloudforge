"""
ec tf action env
ec syn arm --options
ec syn prettify --options

"""
from argparse import ArgumentParser

class BaseCommand:
    def __init__(self):
        self.name = None
        self.desc = None
        self.help_str = None
        self.func = None 
    
    def with_name(self):
        

class ECArgParser(ArgumentParser):
    
    def init(self):
        sub_parser = self.add_subparsers(help='Available subcommands', dest='subcmd')

        tf_subcmd = sub_parser.add_parser('tf', help='Terraform available commands', prefix_chars='tf-')
        tf_subcmd.add_argument("action", choices=['validate', 'deploy'])
        tf_subcmd.add_argument("env", choices=['dev', 'stg', 'uat', 'prod'])
        return self.parse_args()

def execute():
    parser = ECArgParser(prog='ec')
    args = parser.init()
    print(args)