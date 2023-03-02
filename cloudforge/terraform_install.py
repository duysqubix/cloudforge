import os
import platform
import requests
import semantic_version
import tempfile
import zipfile
from pathlib import Path
from typing import Optional


class TerraformInstaller:
    """
    A class that installs the Terraform binary on the local system.

    Attributes:
        _version_index: A dictionary that maps release versions to their metadata.
        _pyos: A string representing the operating system of the local system.
        _arch: A string representing the architecture of the local system.
        _tf_bin: A string representing the path to the Terraform binary.

    Methods:
        __init__: Initializes the TerraformInstaller object.
        install: Downloads and installs the Terraform binary on the local system.
        _get_binary_metadata: Gets the metadata for the Terraform binary of the specified version.
        _download_and_install: Downloads and installs the Terraform binary of the specified version.
        _latest_release_version: Gets the latest release version of Terraform.
        _exact_release_version: Gets the specified version of Terraform.
        __enter__: Enters a context and installs the Terraform binary.
        __exit__: Exits the context and removes the Terraform binary.
    """

    def __init__(self, version: Optional[str] = None, keep_binary=False):
        """
        Initializes the TerraformInstaller object.

        Args:
            version: A string representing the version of Terraform to install.
        """
        tf_index = requests.get(
            "https://releases.hashicorp.com/terraform/index.json"
        ).json()
        self._version_index = {
            semantic_version.Version(k): v for k, v in tf_index["versions"].items()
        }

        self._pyos = platform.system().lower()
        self._arch = platform.machine().lower()

        if self._arch == "x86_64":
            self._arch = "amd64"

        self._tf_bin = None

        self._version = (
            self._latest_release_version()
            if not version
            else self._exact_release_version(version)
        )
        self._keep_binary = keep_binary

    def install(self):
        """
        Downloads and installs the Terraform binary on the local system.
        """
        self._tf_bin = self._download_and_install()

    def _get_binary_metadata(self, version: semantic_version.Version):
        """
        Gets the metadata for the Terraform binary of the specified version.

        Args:
            version: A semantic_version.Version object representing the version of Terraform to install.

        Returns:
            A dictionary containing the metadata for the Terraform binary.
        """
        for build in self._version_index[version]["builds"]:
            if build.get("arch") == self._arch and build.get("os") == self._pyos:
                return build
        raise IndexError("version not found, fatal error")

    def _download_and_install(self):
        """
        Downloads and installs the Terraform binary of the specified version.

        Returns:
            A string representing the path to the Terraform binary.
        """
        mdata = self._get_binary_metadata(self._version)

        url = mdata["url"]

        tf_zip = requests.get(url)

        with tempfile.NamedTemporaryFile(suffix="tf.zip") as zfile:
            zfile.write(tf_zip.content)
            zfile.flush()
            with zipfile.ZipFile(zfile.name) as zip_ref:
                tfbin_path = Path(tempfile.gettempdir()) / (
                    "terraform-" + next(tempfile._get_candidate_names())
                )
                zip_ref.extractall(tfbin_path)

        # finally make terraform executable
        tfbin = tfbin_path / "terraform"
        os.chmod(tfbin, (os.stat(tfbin).st_mode | 0o111))

        return tfbin

    def _latest_release_version(self):
        """
        Gets the latest release version of Terraform.

        Returns:
            A semantic_version.Version object representing the latest release version of Terraform.
        """
        latest_version = max(
            [x for x in self._version_index.keys() if not x.prerelease]
        )
        return latest_version

    def _exact_release_version(self, version: str):
        """
        Gets the specified version of Terraform.

        Args:
            version: A string representing the version of Terraform to install.

        Returns:
            A semantic_version.Version object representing the specified version of Terraform.
        """
        version = semantic_version.Version(version)
        if not self._version_index.get(version):
            raise IndexError("Version does not exist")
        return version

    def __enter__(self):
        """
        Enters a context and installs the Terraform binary.

        Returns:
            The TerraformInstaller object.
        """
        self.install()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the context and removes the Terraform binary.
        """
        # delete binary to free up space
        if not self._keep_binary:
            os.remove(self._tf_bin)

    @property
    def bin_path(self) -> str:
        """
        Gets the path to the Terraform binary.

        Returns:
            A string representing the path to the Terraform binary.
        """
        try:
            return str(self._tf_bin)
        except:
            raise ValueError("tf bin not set -- did it install correctly?")
