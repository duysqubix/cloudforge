"""
common utilities that can be used across multiple scripts
"""
import logging
import os
import re
import subprocess
from typing import Dict, List
from azure.identity._credentials import ClientSecretCredential
from azure.keyvault.secrets import SecretClient, KeyVaultSecret
from pathlib import Path

logging.basicConfig(level=logging.INFO)
TOKEN_RE = re.compile(r"__(.*?)__")


def get_arm_env_variables():
    arm_vars = {k: v for k, v in os.environ.items() if "ARM_" in k}
    return arm_vars


def parse_configuration_file(fpath: Path):
    with open(fpath, 'r') as f:
        contents = f.readlines()

    for line_no, line in enumerate(contents):
        split_line = [word.strip() for word in line.split("=", maxsplit=1)]
        if len(split_line) != 2:
            logging.warning(f"line number {line_no} is not formatted properly")
            logging.warning(split_line)
            continue
        key_name, key_value = split_line
        logging.info(f"Setting environment variable: {key_name}")
        os.environ[key_name] = key_value


def rmdir(dirpath: Path):
    for item in dirpath.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    dirpath.rmdir()


class AzureServicePrincipal:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    def get_client_credentials(self) -> ClientSecretCredential:
        return ClientSecretCredential(client_id=self.client_id,
                                      client_secret=self.client_secret,
                                      tenant_id=self.tenant_id)


class KeyVaultMap:
    """
    Reads arbitrary key vault 
    """
    def __init__(self, auth: AzureServicePrincipal):
        self.key_map: Dict[str, str] = dict()

        self._credential = auth.get_client_credentials()

        self._vault_domain = "https://{vault_name}.vault.azure.net/"

    def get_secrets(self, vault_name) -> Dict[str, KeyVaultSecret]:
        client = SecretClient(
            vault_url=self._vault_domain.format(vault_name=vault_name),
            credential=self._credential)

        key_names: List[str] = list()
        for property in client.list_properties_of_secrets():
            key_names.append(property.name)

        final: Dict[str, KeyVaultSecret] = dict()
        for name in key_names:
            logging.info("Grabbing secret: %s" % name)
            secret = client.get_secret(name)
            final[name] = secret

        return final


class TokenReplacer:
    """
    Reads files in-memory and replaces values based on supplied tokens.
    Writes copies of files to directory
    """
    def __init__(self, dirpath: Path):
        self.tree: Dict[Path, str] = dict()  #[path, content]
        self.root_path = dirpath
        self._read_directory(dirpath)

    def _read_directory(self, dirpath: Path, accepted_extensions=["tf"]):

        for file_extension in accepted_extensions:
            for file in dirpath.glob(f"**/*.{file_extension}"):
                with open(file, 'r') as f:
                    content = f.read()
                self.tree[file] = content

    def replace_tokens(self,
                       token_definitions: Dict[str, str],
                       prefix="__",
                       suffix="__"):
        for file, f_content in self.tree.items():
            logging.info("replacing tokens in %s" % file)
            for token, value in token_definitions.items():
                f_content = f_content.replace(prefix + token + suffix, value)
            self.tree[file] = f_content

    def find_missing_tokens(self):
        validation_errors = list()

        for fpath, content in self.tree.items():
            logging.info("processing %s for missing tokens" % fpath)
            results = TOKEN_RE.findall(content)
            if results is not None:
                validation_errors.extend(results)

        validation_errors = set(validation_errors)
        return validation_errors

    def write_directory(self, dirpath: Path):
        """ 
        creates new files based on tree property to desired dir path
        
        WARNING - No safety nets are in-place to prevent user from overwriting the same
        directory from which you are reading...
        """
        # check if dirpath exists
        try:
            dirpath.mkdir(parents=True, exist_ok=False)
            logging.warning("Directory `%s` does not exist.. creating..." %
                            dirpath)
            # no?
            # create and move on

        except FileExistsError:
            # yes...
            # erase everything and continue
            logging.warning("Directory `%s` exists" % str(dirpath))
            rmdir(dirpath)
            dirpath.mkdir(parents=True, exist_ok=False)

        for fpath, contents in self.tree.items():
            new_path: Path = Path(
                str(fpath).replace(str(self.root_path), str(dirpath)))

            logging.info("[%s]-->[%s]" % (fpath, new_path))
            if new_path.parent != self.root_path:
                new_path.parent.mkdir(parents=True, exist_ok=True)
            with open(new_path, 'w') as f:
                f.write(contents)
                logging.info("writing contents to %s" % new_path)


class AzureTerraform:
    """
    A wrapper class around terraform executable working with Azure
    """
    def __init__(self, storage_account_name: str, sas_token: str,
                 container_name: str, tfkey: str):

        backend_variables = {
            "storage_account_name": storage_account_name,
            "sas_token": sas_token,
            "container_name": container_name,
            "key": tfkey,
        }

        self.backend_config = [
            f"-backend-config={k}={v}" for k, v in backend_variables.items()
        ]

    def init(self, env=None):
        cmd = "terraform init -no-color " + " ".join(self.backend_config)
        _ = subprocess.run(cmd, check=True, shell=True, env=env)

    def validate(self, env=None):
        cmd = "terraform validate -no-color "
        _ = subprocess.run(cmd, check=True, shell=True, env=env)

    def plan(self, env=None):
        cmd = "terraform plan -no-color -out=plan.tfplan"
        _ = subprocess.run(cmd, check=True, shell=True, env=env)

    def apply(self, env=None):
        cmd = "terraform apply -no-color -auto-approve plan.tfplan"
        _ = subprocess.run(cmd, check=True, shell=True, env=env)
