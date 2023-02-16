from pathlib import Path

from . import VALID_ENVS, UnsupportedDevEnvironment
from .utils import EnvConfiguration

import os

class TerraformBinWrapper:
    def __init__(self, env: str) -> None:
        self.env = env.lower()
        
        if self.env not in VALID_ENVS:
            raise UnsupportedDevEnvironment("Invalid environment: %s" % self.env)

    def get_config(self, proj_dir: Path):
        config_file: Path = Path(proj_dir)
        
        config_file /= f".env.{self.env}" # this will dynamically look for the environment based on the `env` supplied
        
        use_arm_env = os.getenv('ARM_VARS_USE_EXISTING')
        
        if not use_arm_env:
            if config_file == Path(proj_dir):
                raise FileNotFoundError("config not set properly: %s" % config_file)
            config = EnvConfiguration(fpath=str(config_file.absolute()))
        else:
            config = EnvConfiguration(fpath=None)
        
        config.read_and_parse()
        return config
    
        

    