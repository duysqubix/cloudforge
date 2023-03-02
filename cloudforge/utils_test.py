import os
from tempfile import NamedTemporaryFile

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
