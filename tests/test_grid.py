# -*- coding: utf-8 -*-
"""
Tests for functionalities in _grid.py.
"""

import geopandas as gpd

import pygeoops
from tests import test_helper


def test_create_grid2():
    # Test for small number of cells
    for i in range(1, 10):
        grid_gdf = pygeoops.create_grid2(
            total_bounds=(40000.0, 160000.0, 45000.0, 210000.0),
            nb_squarish_tiles=i,
            crs="epsg:31370",
        )
        assert len(grid_gdf) == i

    # Test for larger number of cells
    grid_gdf = pygeoops.create_grid2(
        total_bounds=(40000.0, 160000.0, 45000.0, 210000.0),
        nb_squarish_tiles=100,
        crs="epsg:31370",
    )
    assert len(grid_gdf) == 96


def test_split_tiles():
    input_tiles_path = test_helper.get_testfile("BEFL-kbl")
    input_tiles = gpd.read_file(input_tiles_path)
    nb_tiles_wanted = len(input_tiles) * 8
    result = pygeoops.split_tiles(
        input_tiles=input_tiles, nb_tiles_wanted=nb_tiles_wanted
    )

    assert len(result) == len(input_tiles) * 8
