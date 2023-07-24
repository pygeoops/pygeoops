# -*- coding: utf-8 -*-
"""
Tests for functionalities in _grid.py.
"""

import geopandas as gpd
import numpy as np
import pytest

import pygeoops


def test_create_grid():
    grid = pygeoops.create_grid(
        total_bounds=(40000.0, 160000.0, 45000.0, 210000.0), nb_columns=2, nb_rows=2
    )
    assert grid is not None
    assert isinstance(grid, np.ndarray)
    assert len(grid) == 4


def test_create_grid2():
    # Test for small number of cells
    for i in range(1, 10):
        grid = pygeoops.create_grid2(
            total_bounds=(40000.0, 160000.0, 45000.0, 210000.0), nb_squarish_tiles=i
        )
        assert grid is not None
        assert isinstance(grid, np.ndarray)
        assert len(grid) == i

    # Test for larger number of cells
    grid = pygeoops.create_grid2(
        total_bounds=(40000.0, 160000.0, 45000.0, 210000.0), nb_squarish_tiles=100
    )
    assert grid is not None
    assert isinstance(grid, np.ndarray)
    assert len(grid) == 96

    # Test for larger number of cells + nb_squarish_tiles_max
    # Remark: without nb_squarish_tiles_max, nb_squarish_tiles=150 results in 156 tiles
    grid = pygeoops.create_grid2(
        total_bounds=(40000.0, 160000.0, 45000.0, 210000.0),
        nb_squarish_tiles=150,
        nb_squarish_tiles_max=150,
    )
    assert grid is not None
    assert isinstance(grid, np.ndarray)
    assert len(grid) == 148


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
        )


def test_create_grid3():
    bounds = (40000.0, 160000.0, 45000.0, 210000.0)
    grid = pygeoops.create_grid3(
        total_bounds=bounds,
        width=(bounds[2] - bounds[0]) / 2,
        height=(bounds[3] - bounds[1]) / 2,
    )
    assert grid is not None
    assert isinstance(grid, np.ndarray)
    assert len(grid) == 4


@pytest.mark.parametrize(
    "bounds, nb_input_tiles, nb_tiles_wanted, exp_tiles",
    [
        ((40, 40, 45, 46), 4, 8, 8),
        ((40, 40, 45, 46), 4, 12, 12),
        ((40, 40, 46, 45), 4, 8, 8),
        ((40, 40, 46, 45), 4, 12, 12),
        ((40, 40, 45, 45), 4, 2, 4),
    ],
)
def test_split_tiles(bounds, nb_input_tiles, nb_tiles_wanted, exp_tiles):
    # Prepare test data
    nb_input_tiles = 4
    input_tiles = pygeoops.create_grid2(
        total_bounds=bounds, nb_squarish_tiles=nb_input_tiles
    )
    assert len(input_tiles) == nb_input_tiles
    names = {"name": ["foo", "bar", "spam", "ni"]}

    # Test split_tiles
    input_tiles_gdf = gpd.GeoDataFrame(
        data=names, geometry=input_tiles, crs="epsg:31370"
    )
    result_gdf = pygeoops.split_tiles(input_tiles_gdf, nb_tiles_wanted)

    # Check result
    assert result_gdf is not None
    assert isinstance(result_gdf, gpd.GeoDataFrame)
    assert len(result_gdf) == exp_tiles
    # Attribute column data should be retained when a tile is split
    assert "name" in result_gdf.columns
    assert (
        len(result_gdf[result_gdf.name == "spam"])
        / len(input_tiles_gdf[input_tiles_gdf.name == "spam"])
        == exp_tiles / nb_input_tiles
    )
    # Total area of tiles should stay the same after split
    assert input_tiles_gdf.geometry.area.sum() == result_gdf.geometry.area.sum()
