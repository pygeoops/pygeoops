from datetime import datetime
import numpy as np
import pytest
import shapely

import pygeoops
from pygeoops import _difference as difference


def test_difference_all_tiled():
    # None or empty input
    assert pygeoops.difference_all_tiled(None, None) is None
    assert (
        pygeoops.difference_all_tiled(shapely.LineString(), None)
        == shapely.LineString()
    )
    assert pygeoops.difference_all_tiled(shapely.Point(), None) == shapely.Point()
    assert pygeoops.difference_all_tiled(shapely.Polygon(), None) == shapely.Polygon()

    # Single element inputs
    small = shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])
    large = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    assert pygeoops.difference_all_tiled(small, large) == shapely.difference(
        small, large
    )
    assert pygeoops.difference_all_tiled(large, small) == shapely.difference(
        large, small
    )

    # Subtract multiple geometries from single geometry
    small2 = shapely.Polygon([(45, 0), (50, 0), (50, 5), (45, 5), (45, 0)])
    assert pygeoops.difference_all_tiled(large, [small, small2]) == shapely.difference(
        shapely.difference(large, small), small2
    )


def test_difference_all_tiled_complex_poly():
    # Prepare a complex polygon to test with
    poly_size = 1000
    poly_distance = 50
    lines = []
    for off in range(0, poly_size, poly_distance):
        lines.append(shapely.LineString([(off, 0), (off, poly_size)]))
        lines.append(shapely.LineString([(0, off), (poly_size, off)]))

    poly_complex = shapely.unary_union(shapely.MultiLineString(lines).buffer(2))
    poly_complex = shapely.segmentize(poly_complex, max_segment_length=1)
    assert len(shapely.get_parts(poly_complex)) == 1
    assert shapely.get_num_coordinates(poly_complex) == 75574

    # First substract in loop
    number = 500
    start = datetime.now()
    result_shapely = poly_complex
    poly_substract_full = []
    for off in range(0, number, 10):
        poly_substract = shapely.Polygon(
            [(off, off), (off + 9, off), (off + 9, off + 9), (off, off + 9), (off, off)]
        )
        result_shapely = shapely.difference(result_shapely, poly_substract)
        poly_substract_full.append(poly_substract)
    secs_taken_diff = (datetime.now() - start).total_seconds()

    # Now substract using difference_all
    start = datetime.now()
    result_pygeoops = pygeoops.difference_all_tiled(poly_complex, poly_substract_full)
    secs_taken_diff_all = (datetime.now() - start).total_seconds()

    # Result should be about the same, and it should be significantly faster
    assert result_pygeoops.area < poly_complex.area - 400
    assert abs(result_pygeoops.area - result_shapely.area) < 1
    assert secs_taken_diff_all * 2 < secs_taken_diff


def test_difference_all_tiled_invalid_params():
    #
    with pytest.raises(ValueError, match="geometry should be a shapely geometry"):
        pygeoops.difference_all_tiled(
            np.array([shapely.Polygon()]), np.array([shapely.Polygon()])
        )


def test_split_if_needed():
    # Test with complex polygon, it should be split!
    # ----------------------------------------------
    # Prepare a complex polygon to test with
    poly_size = 1000
    poly_distance = 50
    lines = []
    for off in range(0, poly_size, poly_distance):
        lines.append(shapely.LineString([(off, 0), (off, poly_size)]))
        lines.append(shapely.LineString([(0, off), (poly_size, off)]))

    poly_complex = shapely.unary_union(shapely.MultiLineString(lines).buffer(2))
    assert len(shapely.get_parts(poly_complex)) == 1
    num_coordinates = shapely.get_num_coordinates(poly_complex)
    assert num_coordinates == 3258

    num_coords_max = 1000
    poly_split = difference._split_if_needed(poly_complex, num_coords_max)
    assert isinstance(poly_split, np.ndarray)
    assert len(poly_split) == 4

    # Test with standard polygon, should not be split
    # -----------------------------------------------
    poly_simple = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    num_coords_max = 1000
    poly_split = difference._split_if_needed(poly_simple, num_coords_max)
    assert isinstance(poly_split, np.ndarray)
    assert len(poly_split) == 1


def test_difference_intersecting():
    """
    difference_intersecting should, for the cases it supports, return the same values as
    shapely.difference.
    """
    # Single geometry, single geometry_to_subtract
    large = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    small = shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])
    assert difference._difference_intersecting(large, small) == shapely.difference(
        large, small
    )

    # List of input geometries, 1 geometry to subtract
    assert (
        difference._difference_intersecting([large, large], small).tolist()
        == shapely.difference([large, large], small).tolist()
    )

    # Single input geometry, list of geometry to subtract is not supported
    with pytest.raises(ValueError, match="geometry_to_subtract should be geometry"):
        _ = difference._difference_intersecting(large, [small, small])


def test_difference_intersecting_speed():
    """
    This test validates that difference_intersecting is actually faster than vanilla
    shapely.difference.

    It should be faster because it simply combines testing for shapely.intersects and
    running shapely.difference only on elements that actually intersect.
    """
    # Prepare a complex polygon to test with
    poly_size = 300
    poly_distance = 10
    lines = []
    for off in range(0, poly_size, poly_distance):
        lines.append(shapely.LineString([(off, 0), (off, poly_size)]))
        lines.append(shapely.LineString([(0, off), (poly_size, off)]))

    poly_complex = shapely.unary_union(shapely.MultiLineString(lines).buffer(2))
    poly_complex = shapely.segmentize(poly_complex, max_segment_length=1)
    assert len(shapely.get_parts(poly_complex)) == 1
    assert shapely.get_num_coordinates(poly_complex) == 24854

    # Split the complex polygon
    num_coords_max = 800
    poly_split = difference._split_if_needed(poly_complex, num_coords_max)
    assert isinstance(poly_split, np.ndarray)
    assert len(poly_split) == 30

    # Prepare polygon to subtract. For this test case it is given some complexity,
    # without being too large so it doesn't cover too much of the input geometry.
    poly_substract = shapely.Polygon([(50, 50), (90, 50), (90, 90), (50, 90), (50, 50)])
    poly_substract = shapely.segmentize(poly_substract.buffer(10), max_segment_length=1)

    # Calculate difference using shapely
    start = datetime.now()
    _ = shapely.difference(poly_split, poly_substract)
    secs_taken_diff = (datetime.now() - start).total_seconds()

    # Calculate difference using pygeoops
    start = datetime.now()
    _ = difference._difference_intersecting(poly_split, poly_substract)
    secs_taken_diff_intersecting = (datetime.now() - start).total_seconds()

    if secs_taken_diff > 0:
        assert secs_taken_diff_intersecting * 2 < secs_taken_diff