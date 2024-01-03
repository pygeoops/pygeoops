# PyGeoOps

[![Actions Status](https://github.com/pygeoops/pygeoops/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/pygeoops/pygeoops/actions/workflows/tests.yml?query=workflow%3ATests) 
[![codecov](https://codecov.io/gh/pygeoops/pygeoops/branch/main/graph/badge.svg?token=4241CY86O2)](https://codecov.io/gh/pygeoops/pygeoops)
[![PyPI version](https://img.shields.io/pypi/v/pygeoops.svg)](https://pypi.org/project/pygeoops)
[![Conda version](https://anaconda.org/conda-forge/pygeoops/badges/version.svg)](https://anaconda.org/conda-forge/pygeoops)

PyGeoOps provides some less common or extended spatial algorithms and utility functions.

## Introduction

This is a shortlist of the available functions:

* [centerline](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.centerline.html#pygeoops.centerline): centerline/medial axis calculation for a polygon, including optional cleanup of short branches.
* [view_angles](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.view_angles.html#pygeoops.view_angles): determine the start and end angle a polygon is visible from the viewpoint specified
* [simplify](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.simplify.html#pygeoops.simplify): simplify a polygon, with some extended options like
  * choice in simplification algorithms: Lang (+ a variant), Ramer Douglas Peuker, Visvalingal Whyatt
  * specify points/locations where points should not be removed by the simplification
  * topologic simplification: common boundaries between input features should stay common
* utility functions to create and split grids ([create_grid](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.create_grid.html#pygeoops.create_grid), [split_tiles](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.split_tiles.html#pygeoops.split_tiles))
* general utility functions on geometries like [remove_inner_rings](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.remove_inner_rings.html#pygeoops.remove_inner_rings), [collection_extract](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.collection_extract.html),…

Full documentation can be found on [Read the Docs](https://pygeoops.readthedocs.io/en/latest/index.html).

## Usage

The [centerline](https://pygeoops.readthedocs.io/en/latest/api/pygeoops.centerline.html#pygeoops.centerline) for 
a polygon, including the default cleanup of short branches, can be calculated like this:

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
