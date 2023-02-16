import logging 
import tempfile 
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

VALID_ENVS = ["dev", "stg", "uat", "prod"]

TMP_PATH = Path(tempfile.gettempdir()) / ".terraform-py"

class UnsupportedDevEnvironment(Exception):
    pass
