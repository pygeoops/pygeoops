from datetime import datetime

import numpy as np
import pytest
import shapely
import test_helper

import pygeoops
from pygeoops import _difference as difference


def test_difference_all():
    # None or empty input
    # -------------------
    assert pygeoops.difference_all(None, None) is None
    assert pygeoops.difference_all(shapely.LineString(), None) == shapely.LineString()
    assert pygeoops.difference_all(shapely.Point(), None) == shapely.Point()
    assert pygeoops.difference_all(shapely.Polygon(), None) == shapely.Polygon()
    assert (
        pygeoops.difference_all(np.array(shapely.Polygon()), None) == shapely.Polygon()
    )

    # Single element inputs
    # ---------------------
    small = shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])
    large = shapely.Polygon([(0, 2), (50, 2), (50, 50), (0, 50), (0, 2)])
    assert pygeoops.difference_all(small, large) == shapely.difference(small, large)
    assert pygeoops.difference_all(large, small) == shapely.difference(large, small)
    line = shapely.LineString([(0, 0), (50, 0)])
    assert pygeoops.difference_all(line, small) == shapely.difference(line, small)
    assert pygeoops.difference_all(line, small) == shapely.difference(
        np.array(line), np.array(small)
    )

    # Subtract multiple geometries from single geometry
    # -------------------------------------------------
    small2 = shapely.Polygon([(45, 0), (50, 0), (50, 5), (45, 5), (45, 0)])
    assert pygeoops.difference_all(large, [small, small2]) == shapely.difference(
        large, shapely.union_all([small, small2])
    )
    assert pygeoops.difference_all(line, [small, small2]) == shapely.difference(
        line, shapely.union_all([small, small2])
    )
    collection = shapely.GeometryCollection([line, large])
    assert pygeoops.difference_all(collection, [small, small2]) == shapely.difference(
        collection, shapely.union_all([small, small2])
    )

    # Tests with keep_geom_type
    # -------------------------
    # No keep_geom_type: collection (LineString + Polygon)
    assert isinstance(
        pygeoops.difference_all(collection, [small, small2]), shapely.GeometryCollection
    )
    # keep_geom_type=True: collection (LineString + Polygon), because input: collection
    assert isinstance(
        pygeoops.difference_all(collection, [small, small2], keep_geom_type=True),
        shapely.GeometryCollection,
    )
    # keep_geom_type=3: Polygon
    assert isinstance(
        pygeoops.difference_all(collection, [small, small2], keep_geom_type=3),
        shapely.Polygon,
    )
    # keep_geom_type=2: LineString
    assert isinstance(
        pygeoops.difference_all(collection, [small, small2], keep_geom_type=2),
        shapely.LineString,
    )
    # keep_geom_type=1: Point -> None
    assert (
        pygeoops.difference_all(collection, [small, small2], keep_geom_type=1) is None
    )


def test_difference_all_invalid():
    with pytest.raises(ValueError, match="geometry should be a shapely geometry, not"):
        pygeoops.difference_all([shapely.Polygon(), shapely.Polygon()], shapely.Point())


def test_difference_all_tiled():
    # None or empty input
    assert pygeoops.difference_all_tiled(None, None) is None
    assert (
        pygeoops.difference_all_tiled(shapely.LineString(), None)
        == shapely.LineString()
    )
    assert pygeoops.difference_all_tiled(shapely.Point(), None) == shapely.Point()
    assert pygeoops.difference_all_tiled(shapely.Polygon(), None) == shapely.Polygon()
    assert (
        pygeoops.difference_all_tiled(np.array(shapely.Polygon()), None)
        == shapely.Polygon()
    )

    # Single element inputs
    small = shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])
    large = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    assert pygeoops.difference_all_tiled(small, large) == shapely.difference(
        small, large
    )
    assert pygeoops.difference_all_tiled(large, small) == shapely.difference(
        large, small
    )
    assert pygeoops.difference_all_tiled(
        np.array(large), np.array(small)
    ) == shapely.difference(large, small)

    # Subtract multiple geometries from single geometry
    small2 = shapely.Polygon([(45, 0), (50, 0), (50, 5), (45, 5), (45, 0)])
    assert pygeoops.difference_all_tiled(large, [small, small2]) == shapely.difference(
        large, shapely.union_all([small, small2])
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

    # Speed tests only locally, not on CI
    if test_helper.RUNS_LOCAL:
        assert secs_taken_diff_all * 2 < secs_taken_diff


def test_difference_all_tiled_invalid_params():
    with pytest.raises(ValueError, match="geometry should be a shapely geometry"):
        pygeoops.difference_all_tiled(
            np.array([shapely.Polygon()]), np.array([shapely.Polygon()])
        )


def test_difference_intersecting():
    """
    difference_intersecting should return the same values as shapely.difference.

    Only for the cases it supports.
    """
    # None or empty input
    assert difference._difference_intersecting(None, None) is None
    assert (
        difference._difference_intersecting(shapely.LineString(), None)
        == shapely.LineString()
    )
    assert difference._difference_intersecting(shapely.Point(), None) == shapely.Point()
    assert (
        difference._difference_intersecting(shapely.Polygon(), None)
        == shapely.Polygon()
    )
    assert (
        difference._difference_intersecting(np.array(shapely.Polygon()), None)
        == shapely.Polygon()
    )

    # Single geometry, single geometry_to_subtract
    large = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    small = shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])
    assert difference._difference_intersecting(large, small) == shapely.difference(
        large, small
    )
    assert difference._difference_intersecting(
        np.array(large), np.array(small)
    ) == shapely.difference(large, small)

    # Specify keep_geom_type -> only keep points with polygon input -> empty
    assert difference._difference_intersecting(large, small, primitivetype_id=1) is None

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
    poly_divided = pygeoops.subdivide(poly_complex, num_coords_max)
    assert isinstance(poly_divided, np.ndarray)
    assert len(poly_divided) == 30

    # Prepare polygon to subtract. For this test case it is given some complexity,
    # without being too large so it doesn't cover too much of the input geometry.
    poly_substract = shapely.Polygon([(50, 50), (90, 50), (90, 90), (50, 90), (50, 50)])
    poly_substract = shapely.segmentize(poly_substract.buffer(10), max_segment_length=1)

    # Calculate difference using shapely
    start = datetime.now()
    _ = shapely.difference(poly_divided, poly_substract)
    secs_taken_diff = (datetime.now() - start).total_seconds()

    # Calculate difference using pygeoops
    start = datetime.now()
    _ = difference._difference_intersecting(poly_divided, poly_substract)
    secs_taken_diff_intersecting = (datetime.now() - start).total_seconds()

    # Speed tests only locally, not on CI
    if test_helper.RUNS_LOCAL and secs_taken_diff > 0:
        assert secs_taken_diff_intersecting * 2 < secs_taken_diff
