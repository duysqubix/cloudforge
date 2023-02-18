from pathlib import Path

from . import VALID_ENVS, UnsupportedDevEnvironment
from .utils import EnvConfiguration

import os

class TerraformBinWrapper:
    def __init__(self, env: str) -> None:
        self.env = env.lower()
        
        if self.env not in VALID_ENVS:
            raise UnsupportedDevEnvironment("Invalid environment: %s" % self.env)
        
    
        

    