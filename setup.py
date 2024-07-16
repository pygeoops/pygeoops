"""
Setup file to package pygeoops.
"""

import setuptools

with open("pygeoops/version.txt") as file:
    version = file.readline()

setuptools.setup(
    name="pygeoops",
    version=version,
)
