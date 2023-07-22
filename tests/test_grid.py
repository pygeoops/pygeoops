# -*- coding: utf-8 -*-
"""
Tests for functionalities in _grid.py.
"""

import pytest

import pygeoops


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

    # Test for larger number of cells + nb_squarish_tiles_max
    # Remark: without nb_squarish_tiles_max, nb_squarish_tiles=150 results in 156 tiles
    grid_gdf = pygeoops.create_grid2(
        total_bounds=(40000.0, 160000.0, 45000.0, 210000.0),
        nb_squarish_tiles=150,
        nb_squarish_tiles_max=150,
        crs="epsg:31370",
    )
    assert len(grid_gdf) == 148


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
        total_bounds=bounds,
        nb_squarish_tiles=nb_input_tiles,
        crs="epsg:31370",
    )
    assert len(input_tiles) == nb_input_tiles

    # Test split_tiles
    result = pygeoops.split_tiles(input_tiles, nb_tiles_wanted)

    assert len(result) == exp_tiles
    # Total area of tiles should stay the same after split
    assert input_tiles.geometry.area.sum() == result.geometry.area.sum()
