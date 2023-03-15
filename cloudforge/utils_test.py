import os
import pytest

from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock

from .utils import EnvConfiguration


def test_read_and_parse_no_file(monkeypatch):
    # Setup
    expected_key_pairs = dict(os.environ)
    expected_key_pairs["MY_VAR"] = "my_value"
    expected_key_pairs["MY_OTHER_VAR"] = "my_other_value"
    ec = EnvConfiguration()
    monkeypatch.setattr(os, "environ", expected_key_pairs)

    # Exercise
    ec.read_and_parse()

    # Verify
    assert ec.key_pairs == expected_key_pairs


def test_read_and_parse_with_file():
    # Setup
    expected_key_pairs = {"ARM_CLIENT_ID": "12345", "ARM_CLIENT_SECRET": "secret"}
    with NamedTemporaryFile(mode="w") as temp_file:
        temp_file.write("ARM_CLIENT_ID=12345\nARM_CLIENT_SECRET=secret\n")
        temp_file.flush()

        ec = EnvConfiguration(fpath=temp_file.name)

        # Exercise
        ec.read_and_parse()

        # Verify
        assert ec.key_pairs == expected_key_pairs


def test_get_arms():
    # Setup
    key_pairs = {
        "MY_VAR": "my_value",
        "MY_OTHER_VAR": "my_other_value",
        "ARM_CLIENT_ID": "12345",
        "ARM_CLIENT_SECRET": "secret",
        "ARM_TENANT_ID": "67890",
    }
    expected_arms = {
        "ARM_CLIENT_ID": "12345",
        "ARM_CLIENT_SECRET": "secret",
        "ARM_TENANT_ID": "67890",
    }
    ec = EnvConfiguration()
    ec.key_pairs = key_pairs

    # Exercise
    arms = ec.get_arms()

    # Verify
    assert arms == expected_arms


@pytest.fixture
def mock_config_file(tmp_path):
    file = tmp_path / "config.txt"
    file.write_text("a=b")
    return file


@pytest.fixture
def mock_env_variables(monkeypatch):
    monkeypatch.setenv("ARM_VARS_USE_EXISTING", "True")
    return True


def test_load_env_with_file(mock_config_file):
    config = EnvConfiguration.load_env(target_dir_or_file=mock_config_file)
    assert config is not None


def test_load_env_with_dir_and_env(mock_config_file):
    env = "test"
    dir_path = mock_config_file.parent
    config_dir = dir_path / "config"
    config_dir.mkdir()
    config_file = config_dir / f".env.{env}"
    config_file.write_text("a=b\nc=d")
    config = EnvConfiguration.load_env(env=env, target_dir_or_file=config_dir)
    assert config is not None


def test_load_env_with_missing_file():
    with pytest.raises(ValueError):
        EnvConfiguration.load_env(target_dir_or_file="missing_file.txt")


def test_load_env_with_dir_missing_env(mock_config_file):
    dir_path = mock_config_file.parent
    config_dir = dir_path / "doesnotexist"
    config_dir.mkdir()
    with pytest.raises(ValueError):
        EnvConfiguration.load_env(target_dir_or_file=config_dir, env=None)
