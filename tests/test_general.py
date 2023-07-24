# -*- coding: utf-8 -*-
"""
Tests for functionalities in vector_util, regarding geometry operations.
"""

import geopandas as gpd
import numpy as np
import pytest
import shapely

import pygeoops
from pygeoops import PrimitiveType


def test_collect():
    # Test dealing with None/empty input
    # ----------------------------------
    assert pygeoops.collect(None) is None
    assert pygeoops.collect([None]) is None
    # Empty geometries are treated as None as well
    assert pygeoops.collect([None, shapely.Polygon(), None, shapely.Polygon()]) is None

    # Test points
    # -----------
    point = shapely.Point((0, 0))
    assert pygeoops.collect(point) == point
    assert pygeoops.collect([point]) == point
    assert pygeoops.collect([point, point]) == shapely.MultiPoint([(0, 0), (0, 0)])

    # Test linestrings
    # ----------------
    line = shapely.LineString([(0, 0), (0, 1)])
    assert pygeoops.collect(line) == line
    assert pygeoops.collect([line]) == line
    assert pygeoops.collect([line, line]) == shapely.MultiLineString([line, line])

    # Test polygons
    # -------------
    poly = shapely.Polygon([(0, 0), (0, 1), (0, 0)])
    multipoly = shapely.MultiPolygon([poly, poly])
    assert pygeoops.collect(poly) == poly
    assert pygeoops.collect([poly]) == poly
    assert pygeoops.collect([poly, poly]) == multipoly

    # Test geometrycollection
    # -----------------------
    geometrycoll = shapely.GeometryCollection([point, line, poly])
    assert pygeoops.collect(geometrycoll) == geometrycoll
    assert pygeoops.collect([geometrycoll]) == geometrycoll
    assert pygeoops.collect([point, line, poly]) == geometrycoll
    assert pygeoops.collect([geometrycoll, line]) == shapely.GeometryCollection(
        [geometrycoll, line]
    )
    assert pygeoops.collect([poly, multipoly]) == shapely.GeometryCollection(
        [poly, multipoly]
    )

    # Test arraylike input
    # --------------------
    assert pygeoops.collect(gpd.GeoSeries([point, line, poly])) == geometrycoll
    assert pygeoops.collect(np.array([point, line, poly])) == geometrycoll


def test_collection_extract():
    # Test None input
    # ---------------
    assert pygeoops.collection_extract(None, PrimitiveType.POINT) is None
    assert pygeoops.collection_extract([None], PrimitiveType.POINT) == [None]

    # Test dealing with points
    # ------------------------
    point = shapely.Point((0, 0))
    multipoint = shapely.MultiPoint([point, point])
    assert pygeoops.collection_extract(point, PrimitiveType.POINT) == point
    assert pygeoops.collection_extract(multipoint, PrimitiveType.POINT) == multipoint
    assert pygeoops.collection_extract(multipoint, PrimitiveType.POLYGON) is None

    # Test dealing with mixed geometries
    # ----------------------------------
    line = shapely.LineString([(0, 0), (0, 1)])
    poly = shapely.Polygon([(0, 0), (0, 1), (0, 0)])
    multipoly = shapely.MultiPolygon([poly, poly])
    geometrycoll = shapely.GeometryCollection([point, line, poly, multipoly])
    assert pygeoops.collection_extract(geometrycoll, PrimitiveType.POINT) == point
    assert pygeoops.collection_extract(geometrycoll, PrimitiveType.LINESTRING) == line
    assert pygeoops.collection_extract(
        geometrycoll, PrimitiveType.POLYGON
    ) == shapely.GeometryCollection([poly, multipoly])


@pytest.mark.parametrize("input_type", ["geoseries", "ndarray", "list"])
def test_collection_extract_geometries(input_type):
    """
    Test collection_extract with several geometries as input.
    """
    # Prepare test data
    point = shapely.Point((0, 0))
    multipoint = shapely.MultiPoint([point, point])
    line = shapely.LineString([(0, 0), (0, 1)])
    poly = shapely.Polygon([(0, 0), (0, 1), (0, 0)])
    multipoly = shapely.MultiPolygon([poly, poly])
    geometrycoll = shapely.GeometryCollection([point, line, poly, multipoly])
    input = [point, multipoint, line, poly, multipoly, geometrycoll]
    start_idx = 0
    if input_type == "geoseries":
        # For geoseries, also check if the indexers are retained!
        start_idx = 5
        input = gpd.GeoSeries(
            input, index=[index + start_idx for index in range(len(input))]
        )
    elif input_type == "ndarray":
        input = np.array(input)

    # Run test
    result = pygeoops.collection_extract(input, primitivetype=PrimitiveType.POINT)

    # Check result
    assert result is not None
    if input_type == "geoseries":
        assert isinstance(result, gpd.GeoSeries)
    else:
        assert isinstance(result, np.ndarray)
    assert result[start_idx] == point
    assert result[start_idx + 1] == multipoint
    assert result[start_idx + 2] is None
    assert result[start_idx + 3] is None
    assert result[start_idx + 4] is None
    assert result[start_idx + 5] == point


def test_explode():
    # Test dealing with None/empty input
    # ----------------------------------
    assert pygeoops.explode(None) is None

    # Test dealing with points
    # ------------------------
    point = shapely.Point((0, 0))
    multipoint = shapely.MultiPoint([point, point])
    assert pygeoops.explode(point).tolist() == [point]
    assert pygeoops.explode(multipoint).tolist() == [point, point]

    # Test dealing with linestrings
    # -----------------------------
    line = shapely.LineString([(0, 0), (0, 1)])
    multiline = shapely.MultiLineString([line, line])
    assert pygeoops.explode(line).tolist() == [line]
    assert pygeoops.explode(multiline).tolist() == [line, line]

    # Test dealing with Polygons
    # --------------------------
    poly = shapely.Polygon([(0, 0), (0, 1), (0, 0)])
    multipoly = shapely.MultiPolygon([poly, poly])
    assert pygeoops.explode(poly).tolist() == [poly]
    assert pygeoops.explode(multipoly).tolist() == [poly, poly]

    # Test geometrycollection
    # -----------------------
    geometrycoll = shapely.GeometryCollection([point, line, poly])
    assert pygeoops.explode(geometrycoll).tolist() == [point, line, poly]


def test_remove_inner_rings():
    # Test with None input
    assert pygeoops.remove_inner_rings(None, min_area_to_keep=1, crs=None) is None

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
        polygon_removerings_withholes, min_area_to_keep=3, crs="epsg:31370"
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


def test_remove_inner_rings_invalid_input():
    with pytest.raises(ValueError, match="remove_inner_rings impossible on LineString"):
        pygeoops.remove_inner_rings(
            shapely.LineString([(0, 0), (0, 1)]), min_area_to_keep=1, crs=None
        )
