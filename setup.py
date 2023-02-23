import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("pygeoops/version.txt", mode="r") as file:
    version = file.readline()

setuptools.setup(
    name="pygeoops",
    version=version,
    author="Pieter Roggemans",
    author_email="pieter.roggemans@gmail.com",
    description="Library with some spatial algorithms to use on shapely geometries.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pygeoops/pygeoops",
    include_package_data=True,
    packages=setuptools.find_packages(),
    install_requires=[
        "shapely>1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
