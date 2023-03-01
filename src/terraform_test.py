import pytest
from .terraform_install import TerraformInstaller
from pathlib import Path


def test_terraform_installed():
    with TerraformInstaller() as tf:
        assert tf.bin_path.endswith("terraform")


def test_terraform_uninstalled():
    with TerraformInstaller() as tf:
        tfbin = tf.bin_path
        pass
    assert tf._tf_bin.is_file() == False


def test_invalid_version():
    with pytest.raises(IndexError):
        with TerraformInstaller(version="0.12.999") as tf:
            pass
