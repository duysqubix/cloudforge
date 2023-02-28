import logging 
import os 

from . import ECLogger, TMP_DIR
from datetime import datetime 


def test_default_log_level():
    logger = ECLogger()
    assert logger.logger.level == logging.WARNING


def test_custom_log_level():
    logger = ECLogger(level=logging.DEBUG)
    assert logger.logger.level == logging.DEBUG


def test_enable_file_logging():
    logger = ECLogger()
    logger.enable_file_logging()
    
    logger1 = logger.handlers['file_handler']
    passed = False 
    
    for handler in logger.logger.handlers:
        if handler is logger1:
            passed = True
    assert passed == True

def test_disable_file_logging():
    logger = ECLogger()
    logger.enable_file_logging()
    logger.disable_file_logging()
    logger1 = logger.handlers['file_handler']
    exists = False 
    
    for handler in logger.logger.handlers:
        if handler is logger1:
            exists = True
    assert exists == False
    


# def test_log_file_exists():
#     logger = ECLogger()
#     logger.enable_file_logging()
#     logger.warning("test file logging message")
#     now = datetime.now().strftime("%Y%m%d")
#     fname = f".{now}-ec.log"
#     assert os.path.isfile(fname)


def test_log_file_content():

    now = datetime.now().strftime("%Y%m%d")
    fname = f".{now}-ec-test.log"
    open(TMP_DIR / fname, 'w').close()

    logger = ECLogger()
    logger.enable_file_logging(name='ec-test')
    logger.warning("test file logging message")
    

    with open(TMP_DIR / fname, 'r') as f:
        content = f.read().strip()
        assert ("test file logging message" in content) == True