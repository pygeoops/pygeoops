# -*- coding: utf-8 -*-
"""
Tests on lang simplify algorithm.
"""

import numpy as np
import shapely

from pygeoops import _simplify_lang as simplify_lang


def test_simplify_coords_lang_CoordinateSequence():
    # Test LineString, lookahead -1, via coordinates
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    coords_simplified = simplify_lang.simplify_coords_lang(
        coords=linestring.coords, tolerance=1, lookahead=-1
    )
    assert isinstance(coords_simplified, np.ndarray)
    assert len(coords_simplified) < len(linestring.coords)
    assert len(coords_simplified) == 2


def test_simplify_coords_lang_list():
    # Test LineString, lookahead -1, via coordinates
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    coords_simplified = simplify_lang.simplify_coords_lang(
        coords=list(linestring.coords), tolerance=1, lookahead=-1
    )
    assert isinstance(coords_simplified, list)
    assert len(coords_simplified) < len(linestring.coords)
    assert len(coords_simplified) == 2


def test_simplify_coords_lang_ndarray():
    # Test LineString, lookahead -1, via coordinates
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    coords_simplified = simplify_lang.simplify_coords_lang(
        coords=np.asarray(linestring.coords), tolerance=1, lookahead=-1
    )
    assert isinstance(coords_simplified, np.ndarray)
    assert len(coords_simplified) < len(linestring.coords)
    assert len(coords_simplified) == 2


def test_simplify_coords_lang_idx_CoordinateSequence():
    # Test LineString, lookahead -1, via coordinates
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    idx_to_keep = simplify_lang.simplify_coords_lang_idx(
        coords=linestring.coords, tolerance=1, lookahead=-1
    )
    assert isinstance(idx_to_keep, np.ndarray)
    assert len(idx_to_keep) < len(linestring.coords)
    assert len(idx_to_keep) == 2


def test_simplify_coords_lang_idx_list():
    # Test LineString, lookahead -1, via coordinates
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    idx_to_keep = simplify_lang.simplify_coords_lang_idx(
        coords=list(linestring.coords), tolerance=1, lookahead=-1
    )
    assert isinstance(idx_to_keep, list)
    assert len(idx_to_keep) < len(linestring.coords)
    assert len(idx_to_keep) == 2


def test_simplify_coords_lang_idx_ndarray():
    # Test LineString, lookahead -1, via coordinates
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    idx_to_keep = simplify_lang.simplify_coords_lang_idx(
        coords=np.asarray(linestring.coords), tolerance=1, lookahead=-1
    )
    assert isinstance(idx_to_keep, np.ndarray)
    assert len(idx_to_keep) < len(linestring.coords)
    assert len(idx_to_keep) == 2
