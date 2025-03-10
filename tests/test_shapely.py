"""
Some tests mainly meant to explore/show behaviour of some shapely functions.
"""

import numpy as np
import pytest
import shapely
from shapely.testing import assert_geometries_equal


def test_difference():
    # Difference of geom: single geometry, geom_arr: array of 2 geometries
    # Result: 2 rows:
    #   - row 0: difference(geom, geom_arr[0])
    #   - row 1: difference(geom, geom_arr[1])
    geom = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    geom_arr = np.array(
        [
            shapely.Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]),
            shapely.Polygon([(40, 0), (50, 0), (50, 10), (40, 10), (40, 0)]),
        ]
    )
    result = shapely.difference(geom, geom_arr)
    assert len(result) == 2
    assert result[0] == shapely.difference(geom, geom_arr[0])
    assert result[1] == shapely.difference(geom, geom_arr[1])

    # Difference of geom_arr: array of 2 geometries and geom: single geometry
    # Result: 2 rows:
    #   - row 0: difference(geom_arr[0], geom) = empty polygon
    #   - row 1: difference(geom_arr[1], geom) = empty polygon
    result = shapely.difference(geom_arr, geom)
    assert len(result) == 2
    assert result[0] == shapely.difference(geom_arr[0], geom)
    assert result[1] == shapely.difference(geom_arr[1], geom)

    # Difference of:
    #   - geom_arr: array of 2 geometries
    #   - geom_arr2: array of 2 smaller geometries
    # Result: 2 rows:
    #   - row 0: difference(geom_arr[0], geom)
    #   - row 1: difference(geom_arr[1], geom)
    geom_arr2 = np.array(
        [
            shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)]),
            shapely.Polygon([(45, 0), (50, 0), (50, 5), (45, 5), (45, 0)]),
        ]
    )
    result = shapely.difference(geom_arr, geom_arr2)

    assert len(result) == 2
    assert result[0] == shapely.difference(geom_arr[0], geom_arr2[0])
    assert result[1] == shapely.difference(geom_arr[1], geom_arr2[1])

    # Difference of:
    #   - geom_arr: array of 2 geometries
    #   - geom_arr3: array of 3  geometries
    # Result: ValueError, because if both input parameters are arrays, they should be
    # the same length.
    geom_arr3 = np.array(
        [
            shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)]),
            shapely.Polygon([(45, 0), (50, 0), (50, 5), (45, 5), (45, 0)]),
            shapely.Polygon([(45, 0), (50, 0), (50, 5), (45, 5), (45, 0)]),
        ]
    )
    with pytest.raises(ValueError, match="operands could not be broadcast together"):
        _ = shapely.difference(geom_arr, geom_arr3)


def test_difference_collection():
    # Difference of geom: 1 polygon, geom: GeometryCollection of 2 disjoint polygons
    # Result: 1 smaller polygon
    geom = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    geom_collection = shapely.GeometryCollection(
        [
            shapely.Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]),
            shapely.Polygon([(40, 0), (50, 0), (50, 10), (40, 10), (40, 0)]),
        ]
    )
    result = shapely.difference(geom, geom_collection)
    assert result.area < geom.area

    # Difference of geom: 1 polygon, geom: GeometryCollection of 2 adjacent polygons
    # Result: 1 smaller polygon
    geom = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    geom_collection = shapely.GeometryCollection(
        [
            shapely.Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]),
            shapely.Polygon([(10, 0), (20, 0), (20, 10), (10, 10), (10, 0)]),
        ]
    )
    result = shapely.difference(geom, geom_collection)
    assert result.area < geom.area

    # Difference of geom: 1 polygon, geom: GeometryCollection of 2 overlapping polygons
    # Result < GEOS 3.13.1: TopologyException
    geom = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    geom_collection = shapely.GeometryCollection(
        [
            shapely.Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]),
            shapely.Polygon([(5, 0), (20, 0), (20, 10), (5, 10), (5, 0)]),
        ]
    )

    if shapely.geos_version < (3, 13, 1):
        expected_error = (
            "TopologyException: side location conflict at .*. This can occur if the "
            "input geometry is invalid."
        )
        with pytest.raises(Exception, match=expected_error):
            result = shapely.difference(geom, geom_collection)
    else:
        result = shapely.difference(geom, geom_collection)
        assert result.area < geom.area


def test_difference_None_empty():
    assert shapely.difference(None, None) is None
    assert shapely.difference(shapely.Polygon(), None) is None

    # Subtract with None apparently is None
    poly = shapely.Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])
    assert shapely.difference(poly, None) is None

    assert_geometries_equal(
        shapely.difference(poly, shapely.Polygon()), poly, normalize=True
    )
