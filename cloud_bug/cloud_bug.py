"""Main module."""
import http.client
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
import platform
import zipfile

download_base_url = 'https://cloud-debug.amazonwebservices.com/release/metadata'  # 'darwin_amd64/1/latest-version'

class CloudDebug:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/.cloud-bug")
        self.cloud_debug_path = os.path.join(self.base_dir, 'bin', 'cloud-debug')

    def run(self):
        version = latest_version_path()
        self._fetch_if_needed(version)
        result = subprocess.run([self.cloud_debug_path, '-h'])
        print("[INFO] cloud-debug exited with code {}".format(result.returncode))

    def _fetch_if_needed(self, update=False):
        if not update or os.path.exists(self.cloud_debug_path):
            print("[INFO] Skipping cloud-debug download, use --update to force re-downloading")
            return
        else:
            path = latest_version_path()
            print("[INFO] Fetching cloud-debug from {}".format(path))

            zip_path: str
            with urllib.request.urlopen(path) as resp:
                tmp_dir = tempfile.TemporaryDirectory()

                with tempfile.NamedTemporaryFile() as f:
                    zip_path = f.name
                    f.write(resp.read())

                    zipfile.ZipFile(zip_path).extractall(tmp_dir.name)

            src = os.path.join(tmp_dir.name, 'cloud-debug')
            os.makedirs(os.path.dirname(self.cloud_debug_path), exist_ok=True)
            shutil.copy(src, self.cloud_debug_path)
            os.chmod(path=self.cloud_debug_path, mode=0o755)

            print("[INFO] cloud-debug downloaded and extracted to {}.".format(self.cloud_debug_path))


def latest_version_path() -> str:
    sys = platform.system()
    sys_url_part: str
    if sys == 'Darwin':
        sys_url_part = 'darwin_amd64'
    elif sys == 'Linux':
        raise NotImplemented
    elif sys == 'Windows':
        raise NotImplemented
    else:
        raise UserWarning("Unknown system type: {}".format(sys))

    # TODO: Don't hardcode minor version, can get this at '/1/latest-version'
    path = '{}/{}/1/1.0/latest-version'.format(download_base_url, sys_url_part)

    version: str
    with urllib.request.urlopen(path) as f:
        version = f.read().decode('utf-8')

    metadata_path = '{}/{}/1/1.0/{}/release-metadata.json'.format(download_base_url, sys_url_part, version)

    metadata: dict  # { "location":"...", "checksum":"...", ... }
    print('[INFO] Fetching metadata from {}'.format(metadata_path))
    with urllib.request.urlopen(metadata_path) as f:
        metadata = json.loads(f.read().decode('utf-8'))

    return metadata["location"]
