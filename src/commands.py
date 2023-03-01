"""
ec tf action env
ec syn arm --options
ec syn prettify --options

"""
from argparse import ArgumentParser, Namespace
from pathlib import Path
from azure.identity import ClientSecretCredential


from . import TMP_PATH, logger, TMP_DIR
from .tokenizer import Tokenizer
from .terraform import TerraformBinWrapper
from .terraform_install import TerraformInstaller
from .terraform_exec import Terraform
from .keyvault import AzureKeyVault
from .utils import EnvConfiguration

import shutil
import platform
import os
import sys


class BaseCommand:
    def __init__(self, args: Namespace, skip_setup=False) -> None:
        self._args = args

        if not skip_setup:
            self.setup()

    def setup(self):
        pass


class CleanCommands(BaseCommand):
    def setup(self):
        self.module_to_clean = self._args.module

    def execute(self):
        if self.module_to_clean == "all":
            self._clean_up_ectf_files()

        elif self.module_to_clean == "ectf":
            self._clean_up_ectf_files()

    def _clean_up_ectf_files(self):
        for fobj in TMP_DIR.glob("*"):
            if "terraform" in fobj.name:
                if fobj.is_dir():
                    logger.warning(f"Removing {fobj}")
                    shutil.rmtree(fobj)

                if fobj.is_file():
                    logger.warning(f"Removing {fobj}")
                    fobj.unlink()


class TerraformCommands(BaseCommand):
    def setup(self) -> None:
        self.targeted_action = self._args.action
        self.tf = TerraformBinWrapper(self._args.env)

        self.tokenizer = Tokenizer(self._args.proj_dir, "tf")
        self.tokenizer.read_root()

        self.config = EnvConfiguration.load_env(self.tf.env, self._args.proj_dir)

        vault_name = self.config.get("KEY_VAULT_NAME")

        auth = ClientSecretCredential(**self.config.get_terraform_creds())
        tokens = AzureKeyVault(vault_name, auth).get_secrets()

        # get secrets from Key Vault
        parsed_tree = self.tokenizer.replace_and_validate_tokens(tokens)

        self.tmp_dir = self.tokenizer.dump_to(
            tree=parsed_tree, dirpath=TMP_PATH, unique=True
        )

        self.backend_config = {
            "storage_account_name": self.config.get("STORAGE_ACCOUNT_NAME"),
            "sas_token": self.config.get("SAS_TOKEN"),
            "key": self.config.get("TF_KEY"),
            "container_name": self.config.get("CONTAINER_NAME"),
        }

        self.arm_config = {
            "ARM_CLIENT_ID": self.config.get("ARM_CLIENT_ID"),
            "ARM_CLIENT_SECRET": self.config.get("ARM_CLIENT_SECRET"),
            "ARM_TENANT_ID": self.config.get("ARM_TENANT_ID"),
            "ARM_SUBSCRIPTION_ID": self.config.get("ARM_SUBSCRIPTION_ID"),
        }

    def _run_tf_cmd(self, cmd, **kwargs):
        options = kwargs.copy()

        options["raise_on_error"] = False
        options["capture_output"] = True

        ret_code, msg, err_msg = cmd(**options)
        if ret_code != 0:
            self._clean_up()
            logger.error(f"CMD: tf.{cmd.__name__}() raised error.. aborting")
            logger.error(err_msg)
            sys.exit(ret_code)
        logger.info(msg)

    def _clean_up(self):
        logger.warning(f"Removing directory: {self.tmp_dir.absolute()}")
        shutil.rmtree(self.tmp_dir)  # clean up

    def execute(self):
        if self.targeted_action in ("validate", "deploy"):
            with TerraformInstaller(keep_binary=False) as tf_installer:
                self.config.ensure_arms_in_env()  # this ensures arm credentials are set in os environment, used by Terraform binary
                ectf_dir = str(self.tmp_dir.absolute())

                tf = Terraform(
                    terraform_bin_path=tf_installer.bin_path,
                    working_dir=ectf_dir,
                    is_env_vars_included=True,
                )

                self._run_tf_cmd(
                    tf.init,
                    backend_config=self.backend_config,
                    backend=True,
                    reconfigure=False,
                )

                if self.targeted_action == "validate":
                    self._run_tf_cmd(tf.validate)
                    self._run_tf_cmd(tf.plan, detailed_exitcode=False)

                if self.targeted_action == "deploy":
                    self._run_tf_cmd(tf.apply, skip_plan=True)

            self._clean_up()

        elif self.targeted_action == "debug":
            self._handle_debug_action()

    def _handle_debug_action(self):
        if platform.system() != "Linux":
            raise OSError(
                "Debug command does not work in a windows environment, please switch to an OS that supports Bash Scripting"
            )

        init_fname = "init.sh"
        wrapper_fname = "terraform.sh"

        prefix_str = ""
        for k, v in self.arm_config.items():
            prefix_str += f"{k}={v} "

        backend_configs = ""
        for k, v in self.backend_config.items():
            backend_configs += f"-backend-config={k}={v} "

        init_path = self.tmp_dir / init_fname
        wrapper_path = self.tmp_dir / wrapper_fname

        with open(init_path, "w") as init_f:
            script_str = f"{prefix_str}terraform init {backend_configs}"
            init_f.write(script_str)
            logger.info(f"Writing to: {init_path}")

        with open(wrapper_path, "w") as wrapper_f:
            script_str = "#!/usr/bin/env bash\n\n" + f"{prefix_str}terraform $@"
            wrapper_f.write(script_str)
            logger.info(f"Writing to: {wrapper_path}")

        os.chmod(init_path, 0o700)
        os.chmod(wrapper_path, 0o700)
        logger.warning(f"Debug environment created in: {self.tmp_dir}")
        logger.warning("Please take caution and remove directory when done.")


class ECArgParser(ArgumentParser):
    def init(self):
        self.add_argument(
            "-v", "--verbose", action="store_true", help="Enable verbose mode"
        )
        self.sub_parser = self.add_subparsers(
            help="Available subcommands", dest="subcmd"
        )

        self._setup_terraform_subcommand()
        self._setup_clean_subcommand()

        return self.parse_args()

    def _setup_terraform_subcommand(self):
        tf_subcmd = self.sub_parser.add_parser(
            "tf", help="Terraform available commands", prefix_chars="tf-"
        )
        tf_subcmd.add_argument(
            "action",
            choices=["validate", "deploy", "debug", "clean"],
            help="Choose an action",
        )
        tf_subcmd.add_argument(
            "env",
            choices=["dev", "stg", "uat", "prod"],
            help="Choose an targeted environment",
        )
        tf_subcmd.add_argument(
            "-d",
            "--proj-dir",
            default=str(Path.cwd().absolute()),
            type=lambda x: Path(x),
            help=f"Define the project directory that holds ECTF files. Default: {str(Path.cwd().absolute())}",
        )

    def _setup_
    
    def _setup_clean_subcommand(self):
        clean_subcmd = self.sub_parser.add_parser(
            "clean",
            help="helper utilities to clean up artifacts left by ec",
            prefix_chars="c-",
        )
        clean_subcmd.add_argument(
            "module", choices=["ectf", "all"], help="Clean up artifacts left by ec."
        )


def execute():
    parser = ECArgParser(prog="ec")
    args = parser.init()

    subcmd_mapping = {"tf": TerraformCommands, "clean": CleanCommands}

    if args.verbose:
        logger.enable_debug()
        logger.enable_file_logging()

    subcmd = subcmd_mapping.get(args.subcmd)

    if not subcmd:
        parser.print_help()
        return

    subcmd(args).execute()

    if args.verbose:
        logger.disable_debug()
        logger.disable_file_logging()
