# -*- coding: utf-8 -*-
"""
Tests for functionalities in vector_util, regarding geometry operations.
"""

import shapely

import pygeoops
import test_helper


def test_numberpoints():
    # Test Point
    numberpoints = pygeoops.numberpoints(test_helper.TestData.point)
    numberpoints_geometrycollection = numberpoints
    assert numberpoints == 1

    # Test MultiPoint
    numberpoints = pygeoops.numberpoints(test_helper.TestData.multipoint)
    numberpoints_geometrycollection += numberpoints
    assert numberpoints == 3

    # Test LineString
    numberpoints = pygeoops.numberpoints(test_helper.TestData.linestring)
    numberpoints_geometrycollection += numberpoints
    assert numberpoints == 3

    # Test MultiLineString
    numberpoints = pygeoops.numberpoints(test_helper.TestData.multilinestring)
    numberpoints_geometrycollection += numberpoints
    assert numberpoints == 6

    # Test Polygon
    numberpoints = pygeoops.numberpoints(test_helper.TestData.polygon_with_island)
    numberpoints_geometrycollection += numberpoints
    assert numberpoints == 11

    # Test MultiPolygon
    numberpoints = pygeoops.numberpoints(test_helper.TestData.multipolygon)
    numberpoints_geometrycollection += numberpoints
    assert numberpoints == 16

    # Test GeometryCollection (as combination of all previous ones)
    numberpoints = pygeoops.numberpoints(test_helper.TestData.geometrycollection)
    assert numberpoints == numberpoints_geometrycollection


def test_remove_inner_rings():
    # Apply to single Polygon, with area tolerance smaller than holes
    polygon_removerings_withholes = shapely.Polygon(
        shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
        holes=[
            [(2, 2), (2, 4), (4, 4), (4, 2), (2, 2)],
            [(5, 5), (5, 6), (7, 6), (7, 5), (5, 5)],
        ],
    )
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_withholes, min_area_to_keep=1, crs=None
    )
    assert isinstance(poly_result, shapely.Polygon)
    assert len(poly_result.interiors) == 2

    # Apply to single Polygon, with area tolerance between
    # smallest hole (= 2m²) and largest (= 4m²)
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_withholes, min_area_to_keep=3, crs=None
    )
    assert isinstance(poly_result, shapely.Polygon)
    assert len(poly_result.interiors) == 1

    # Apply to single polygon and remove all holes
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_withholes, min_area_to_keep=0, crs=None
    )
    assert isinstance(poly_result, shapely.Polygon)
    assert len(poly_result.interiors) == 0
    polygon_removerings_noholes = shapely.Polygon(
        shell=[(100, 100), (100, 110), (110, 110), (110, 100), (100, 100)]
    )
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_noholes, min_area_to_keep=0, crs=None
    )
    assert isinstance(poly_result, shapely.Polygon)
    assert len(poly_result.interiors) == 0

    # Apply to MultiPolygon, with area tolerance between
    # smallest hole (= 2m²) and largest (= 4m²)
    multipoly_removerings = shapely.MultiPolygon(
        [polygon_removerings_withholes, polygon_removerings_noholes]
    )
    poly_result = pygeoops.remove_inner_rings(
        multipoly_removerings, min_area_to_keep=3, crs=None
    )
    assert isinstance(poly_result, shapely.MultiPolygon)
    interiors = poly_result.geoms[
        0
    ].interiors  # pyright: ignore[reportOptionalMemberAccess]
    assert len(interiors) == 1
