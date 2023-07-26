# -*- coding: utf-8 -*-
"""
Tests on lang simplify algorithm.
"""

import numpy as np
import pytest
import shapely

from pygeoops import _simplify_lang as simplify_lang


def test_simplify_coords_lang_simplify_lookahead_points():
    """
    In the standard lang algorithm the window_end is never masked, so with e.g.
    lookahead=3 the simplified version still has minimally ~33% of the input points.

    This test tests the tweak in the pygeoops algorithm to avoid this limitation.
    """
    # Prepare test data
    linestring = shapely.LineString(
        [(0, 0), (10, 10), (20, 20), (30, 30), (40, 40), (50, 30), (60, 20), (70, 10)]
    )
    # With lookahead=3, the 4rd point, (30, 30), would never be removed using the
    # standard LANG algorithm even though it is collinear with the points around it.
    lookahead = 3

    # Run test
    coords_simplified = simplify_lang.simplify_coords_lang(
        coords=linestring.coords,
        tolerance=1,
        lookahead=lookahead,
        simplify_lookahead_points=True,
    )

    # Check result
    assert coords_simplified is not None
    assert isinstance(coords_simplified, np.ndarray)
    assert len(coords_simplified) < len(linestring.coords)
    assert len(coords_simplified) == 3


@pytest.mark.parametrize("input_type", ["coordinatesequence", "list", "ndarray"])
def test_simplify_coords_lang_input_types(input_type):
    # Prepare test data
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20), (30, 30), (40, 40)])
    coords = linestring.coords
    if input_type == "list":
        coords = list(coords)
    elif input_type == "ndarray":
        coords = np.asarray(coords)

    # Run test
    coords_simplified = simplify_lang.simplify_coords_lang(coords=coords, tolerance=1)

    # Check result
    if input_type == "list":
        assert isinstance(coords_simplified, list)
    else:
        assert isinstance(coords_simplified, np.ndarray)
    assert len(coords_simplified) < len(coords)
    assert len(coords_simplified) == 2


@pytest.mark.parametrize("input_type", ["coordinatesequence", "list", "ndarray"])
def test_simplify_coords_lang_idx_input_types(input_type):
    # Prepare test data
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    coords = linestring.coords
    if input_type == "list":
        coords = list(coords)
    elif input_type == "ndarray":
        coords = np.asarray(coords)

    # Run test
    idx_to_keep = simplify_lang.simplify_coords_lang_idx(coords=coords, tolerance=1)

    # Check result
    if input_type == "list":
        assert isinstance(idx_to_keep, list)
    else:
        assert isinstance(idx_to_keep, np.ndarray)
    assert len(idx_to_keep) < len(coords)
    assert len(idx_to_keep) == 2
