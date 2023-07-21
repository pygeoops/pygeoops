# -*- coding: utf-8 -*-
"""
Tests for functionalities in _grid.py.
"""

import geopandas as gpd
import pytest

import pygeoops
import test_helper


def test_create_grid():
    grid_gdf = pygeoops.create_grid(
        total_bounds=(40000.0, 160000.0, 45000.0, 210000.0),
        nb_columns=2,
        nb_rows=2,
        crs="epsg:31370",
    )
    assert len(grid_gdf) == 4


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


@pytest.mark.parametrize(
    "exp_error, nb_squarish_tiles, nb_squarish_tiles_max",
    [
        ("nb_squarish_tiles_max should be > 0", 1, 0),
        ("nb_squarish_tiles_max should be >= nb_squarich_tiles", 4, 3),
        ("nb_squarish_tiles should be > 0", 0, None),
    ],
)
def test_create_grid2_invalid_params(
    exp_error, nb_squarish_tiles, nb_squarish_tiles_max
):
    # Test for invalid number of nb_squarish_tiles_max
    with pytest.raises(ValueError, match=exp_error):
        _ = pygeoops.create_grid2(
            total_bounds=(40000.0, 160000.0, 45000.0, 210000.0),
            nb_squarish_tiles=nb_squarish_tiles,
            nb_squarish_tiles_max=nb_squarish_tiles_max,
            crs="epsg:31370",
        )


def test_create_grid3():
    bounds = (40000.0, 160000.0, 45000.0, 210000.0)
    grid_gdf = pygeoops.create_grid3(
        total_bounds=bounds,
        width=(bounds[2] - bounds[0]) / 2,
        height=(bounds[3] - bounds[1]) / 2,
        crs="epsg:31370",
    )
    assert len(grid_gdf) == 4


def test_split_tiles():
    input_tiles_path = test_helper.get_testfile("BEFL-kbl")
    input_tiles = gpd.read_file(input_tiles_path)
    nb_tiles_wanted = len(input_tiles) * 8
    result = pygeoops.split_tiles(
        input_tiles=input_tiles, nb_tiles_wanted=nb_tiles_wanted
    )

    assert len(result) == len(input_tiles) * 8
