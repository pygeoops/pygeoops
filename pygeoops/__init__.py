from pathlib import Path

from pygeoops.centerline import *
from pygeoops.view_angles import *


def _get_version():
    version_path = Path(__file__).resolve().parent / "version.txt"
    with open(version_path, mode="r") as file:
        return file.readline()


__version__ = _get_version()
