"""
Library with some less common or extended spatial functions.
"""

from pathlib import Path

from pygeoops._buffer_by_m import *  # noqa: F403
from pygeoops._centerline import *  # noqa: F403
from pygeoops._difference import *  # noqa: F403
from pygeoops._extend_line import *  # noqa: F403
from pygeoops._general import *  # noqa: F403
from pygeoops._grid import *  # noqa: F403
from pygeoops._simplify import *  # noqa: F403
from pygeoops._types import *  # noqa: F403
from pygeoops._view_angles import *  # noqa: F403


def _get_version():
    version_path = Path(__file__).resolve().parent / "version.txt"
    with open(version_path) as file:
        return file.readline()


__version__ = _get_version()
