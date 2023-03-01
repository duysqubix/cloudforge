from pathlib import Path

from . import VALID_ENVS, UnsupportedDevEnvironment
from .utils import EnvConfiguration

import os

# find the terraform index.json
# at
# https://releases.hashicorp.com/terraform/index.json


class TerraformBinWrapper:
    def __init__(self, env: str) -> None:
        self.env = env.lower()

        if self.env not in VALID_ENVS:
            raise UnsupportedDevEnvironment("Invalid environment: %s" % self.env)
