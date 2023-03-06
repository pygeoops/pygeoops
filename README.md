# PyGeoOps

[![Actions Status](https://github.com/pygeoops/pygeoops/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/pygeoops/pygeoops/actions/workflows/tests.yml?query=workflow%3ATests) 
[![codecov](https://codecov.io/gh/pygeoops/pygeoops/branch/main/graph/badge.svg?token=4241CY86O2)](https://codecov.io/gh/pygeoops/pygeoops)
[![PyPI version](https://img.shields.io/pypi/v/pygeoops.svg)](https://pypi.org/project/pygeoops)
[![Conda version](https://anaconda.org/conda-forge/pygeoops/badges/version.svg)](https://anaconda.org/conda-forge/pygeoops)

PyGeoOps provides some less common or extended spatial algorithms and utility functions.

## Usage

Calculate a [centerline](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.centerline.html#pygeoops.centerline) for a polygon:

```
import pygeoops
import shapely

polygon = shapely.from_wkt("POLYGON ((0 0, 0 8, -2 10, 4 10, 2 8, 2 2, 10 2, 10 0, 0 0))")
centerline = pygeoops.centerline(polygon)
```
![centerline](https://github.com/pygeoops/pygeoops/blob/main/docs/_static/images/centerline_fancy_Lshape.png)

## Installation

PyGeoOps is available on PyPi, so can be installed using pip:

```
pip install pygeoops
```

Another option is to use conda or mamba, as it is also available on conda-forge:

```
conda install pygeoops --channel conda-forge
```
