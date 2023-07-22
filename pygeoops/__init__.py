from pathlib import Path

from pygeoops._centerline import *  # noqa: F403
from pygeoops._general import *  # noqa: F403
from pygeoops._grid import *  # noqa: F403
from pygeoops._simplify import *  # noqa: F403
from pygeoops._types import *  # noqa: F403
from pygeoops._view_angles import *  # noqa: F403


def _get_version():
    version_path = Path(__file__).resolve().parent / "version.txt"
    with open(version_path, mode="r") as file:
        return file.readline()


__version__ = _get_version()
