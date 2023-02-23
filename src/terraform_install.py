from typing import Optional 
from pathlib import Path

import json
import requests 
import semantic_version
import platform
import uuid 
import tempfile
import zipfile
import os



class TerraformInstaller:
    def __init__(self, version: Optional[str] = None):
        tf_index = requests.get("https://releases.hashicorp.com/terraform/index.json").json()
        self._version_index = {
            semantic_version.Version(k):v for k,v in tf_index['versions'].items()
        }

        self._pyos = platform.system().lower()
        self._arch = platform.machine().lower()
        
        if self._arch == "x86_64":
            self._arch = "amd64"
            
        self._tf_bin = None
        
        self._version = self._latest_release_version() if not version else self._exact_release_version(version)
    
    def install(self):
        self._tf_bin = self._download_and_install()
    
    def _get_binary_metadata(self, version: semantic_version.Version):
        for build in self._version_index[version]['builds']:
            if build.get('arch') == self._arch and build.get('os') == self._pyos:
                return build 
        raise IndexError('version not found, fatal error')
    
    def _download_and_install(self):
        mdata = self._get_binary_metadata(self._version)
        
        url = mdata['url']
        
        tf_zip = requests.get(url)
        
        with tempfile.NamedTemporaryFile(suffix="tf.zip") as zfile:
            zfile.write(tf_zip.content)
            zfile.flush()
            with zipfile.ZipFile(zfile.name) as zip_ref:
                tfbin_path = Path(tempfile.gettempdir()) / ("terraform-" + next(tempfile._get_candidate_names()))
                zip_ref.extractall(tfbin_path)
        
        # finally make terraform executable
        tfbin = tfbin_path / "terraform"
        os.chmod(tfbin, (os.stat(tfbin).st_mode | 0o111))
        return tfbin
    
    def _latest_release_version(self):
        latest_version = max([x for x in self._version_index.keys() if not x.prerelease])
        return latest_version
    
    def _exact_release_version(self, version: str):
        version = semantic_version.Version(version)
        if not self._version_index.get(version):
            raise IndexError('Version does not exist')
        return version
    
    def __enter__(self):
        self.install()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # delete binary to free up space
        os.remove(self._tf_bin)
        
    @property
    def bin_path(self):
        try:
            return str(self._tf_bin)
        except:
            raise ValueError("tf bin not set -- did it install correctly?")

if __name__ == "__main__":
    with TerraformInstaller() as tf:
        print(tf._tf_bin)