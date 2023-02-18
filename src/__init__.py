import logging 
import tempfile 
from pathlib import Path


VALID_ENVS = ["dev", "stg", "uat", "prod"]

TMP_PATH = Path(tempfile.gettempdir()) / ".terraform-py"

class UnsupportedDevEnvironment(Exception):
    pass
