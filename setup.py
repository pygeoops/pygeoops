import setuptools

with open("pygeoops/version.txt", mode="r") as file:
    version = file.readline()

setuptools.setup(
    name="pygeoops",
    version=version,
)
