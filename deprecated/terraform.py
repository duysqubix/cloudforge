""" 
Deploys current terraform into the development environment


# Note - If running headless or wanting to NOT use a configuration file
make sure to set the following environment variable to non-null or empty.

ARM_VARS_USE_EXISTING
"""
try:
    import logging
    import coloredlogs
    coloredlogs.install()
finally:
    import logging

import re
import os
import argparse
from pathlib import Path

from utils.utils import KeyVaultMap, AzureServicePrincipal, get_arm_env_variables, parse_configuration_file, TokenReplacer, AzureTerraform

TOKEN_RE = re.compile(r"__(.*?)__")

parser = argparse.ArgumentParser()
parser.add_argument("--deploy",
                    help="deploys terraform to development environment",
                    action="store_true")

parser.add_argument(
    "--config",
    help="relative path to configuration file that holds credentials",
    required=False)

parser.add_argument("--validate",
                    nargs="+",
                    help="Runs validation routine",
                    required=False)


def get_sensitive_data():
    return {
        "client_id": os.environ['ARM_CLIENT_ID'],
        "client_secret": os.environ['ARM_CLIENT_SECRET'],
        "tenant_id": os.environ['ARM_TENANT_ID'],
        "storage_account_name": os.environ['STORAGE_ACCOUNT_NAME'],
        "sas_token": os.environ['SAS_TOKEN'],
        "container_name": os.environ['CONTAINER_NAME'],
        "tf_key": os.environ['TF_KEY'],
        "key_vault_name": os.environ['KEY_VAULT_NAME']
    }


def get_main_objects_related_to(fname):
    """
    returns token_definitions, terraform, and tokenizier objects 
    this is a helper func
    """

    if not os.environ.get("ARM_VARS_USE_EXISTING"):
        # parse configuration file for use with authentication with azure
        # and terraform
        parse_configuration_file(fname)

    # # retrieve sensitive values from environment variables
    creds = get_sensitive_data()
    # create authenciation object via Service Principal
    auth = AzureServicePrincipal(creds.get("client_id"),
                                 creds.get("client_secret"),
                                 creds.get("tenant_id"))

    # Initialize tokenizer used for replacing tokens within file
    tokenizer = TokenReplacer(Path(__file__).resolve().parents[1])

    # initialize keyvault object
    kvm = KeyVaultMap(auth)
    terraform = AzureTerraform(
        storage_account_name=creds.get("storage_account_name"),
        sas_token=creds.get("sas_token"),
        container_name=creds.get("container_name"),
        tfkey=creds.get("tf_key"))

    # create token definitions from KeyVaultMap
    token_definitions = {
        key: value.value
        for key, value in kvm.get_secrets(creds.get("key_vault_name")).items()
    }
    return terraform, token_definitions, tokenizer


def validate_terraform(args: argparse.Namespace):
    orig_dir = Path(__file__).parent.resolve()
    all_envs = {"dev", "int", "uat", "prod"}
    selected_envs = set([x.lower() for x in args.validate])

    test_mapping = {"dev": False, "int": False, "uat": False, "prod": False}

    valid_envs = all_envs & selected_envs
    for env in valid_envs:
        test_mapping.update({env: True})

    for env, test_status in test_mapping.items():
        if not test_status:
            logging.warning("skipping environment: %s" % env)
            continue
        logging.info("Beginning testings of.....[%s]" % env)

        terraform, token_definitions, tokenizer = get_main_objects_related_to(
            f".env.{env}")

        tokenizer.replace_tokens(token_definitions)

        validation_errors = tokenizer.find_missing_tokens()
        if validation_errors:
            raise Exception(
                f"Validation error, unused tokens found:\n{validation_errors}")

        tmp_dir = Path("/tmp/.terraformvalidation")
        tokenizer.write_directory(tmp_dir)
        os.chdir(tmp_dir)
        arm_vars = {k: v for k, v in os.environ.items() if "ARM_" in k}

        terraform.init(arm_vars)
        terraform.validate(arm_vars)

        logging.info("Moving back to original directory: %s" % orig_dir)
        os.chdir(orig_dir)


def main():
    args = parser.parse_args()

    if bool(args.validate) is True:
        validate_terraform(args)
        return

    if not args.config and not os.environ.get("ARM_VARS_USE_EXISTING"):
        logging.error(
            "missing configuration file path or forgot to set ARM_VARS_USE_EXISTING variable"
        )
        return

    if args.config and os.environ.get("ARM_VARS_USE_EXISTING"):
        logging.warning(
            "config set AND ARM_VARS_USE_EXISTING is set. config taking precedence."
        )
        del os.environ["ARM_VARS_USE_EXISTING"]

    terraform, token_definitions, tokenizer = get_main_objects_related_to(
        args.config)

    # replace tokens
    tokenizer.replace_tokens(token_definitions)

    # identify errors
    validation_errors = tokenizer.find_missing_tokens()
    if validation_errors:
        logging.error("Tokens not set: %s" % str(validation_errors))
        return

    # write to new directory
    tmp_dir = Path("/tmp/.tmpterraform")
    tokenizer.write_directory(tmp_dir)

    # move to new directory
    os.chdir(tmp_dir)
    # get ARM_variables
    arm_vars = get_arm_env_variables()
    # execute terraform commands
    terraform.init(arm_vars)
    terraform.plan(arm_vars)

    if args.deploy:
        terraform.apply(arm_vars)


if __name__ == '__main__':
    main()
