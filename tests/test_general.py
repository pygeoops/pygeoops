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
    """
    Base tests
    """
    # Test None input
    # ---------------
    assert pygeoops.collection_extract(None, 0) is None
    assert pygeoops.collection_extract([None], 0) == [None]

    # Test dealing with points
    # ------------------------
    point = shapely.Point((0, 0))
    multipoint = shapely.MultiPoint([point, point])
    assert pygeoops.collection_extract(point, 1) == point
    assert pygeoops.collection_extract(multipoint, 1) == multipoint
    assert pygeoops.collection_extract(multipoint, 2) is None

    # Test dealing with mixed geometries
    # ----------------------------------
    line = shapely.LineString([(0, 0), (0, 1)])
    poly = shapely.Polygon([(0, 0), (0, 1), (0, 0)])
    multipoly = shapely.MultiPolygon([poly, poly])
    geometrycoll = shapely.GeometryCollection([point, line, poly, multipoly])
    assert pygeoops.collection_extract(geometrycoll, 1) == point
    assert pygeoops.collection_extract(geometrycoll, PrimitiveType.POINT) == point
    assert pygeoops.collection_extract(geometrycoll, 2) == line
    assert pygeoops.collection_extract(geometrycoll, PrimitiveType.LINESTRING) == line
    assert pygeoops.collection_extract(geometrycoll, 3) == shapely.GeometryCollection(
        [poly, multipoly]
    )
    assert pygeoops.collection_extract(
        geometrycoll, PrimitiveType.POLYGON
    ) == shapely.GeometryCollection([poly, multipoly])
    assert pygeoops.collection_extract(geometrycoll, 0) == geometrycoll

    # Test dealing with deeper nested geometries
    # ------------------------------------------
    assert pygeoops.collection_extract(
        shapely.GeometryCollection(geometrycoll), 0
    ) == shapely.GeometryCollection(geometrycoll)


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
    result = pygeoops.collection_extract(input, primitivetype=1)

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


def test_collection_extract_invalid_params():
    with pytest.raises(ValueError, match="Invalid value for primitivetype: 5"):
        pygeoops.collection_extract(shapely.Point((0, 0)), primitivetype=5)
    with pytest.raises(ValueError, match="Invalid value for primitivetype: -5"):
        pygeoops.collection_extract(shapely.Point((0, 0)), primitivetype=-5)
    with pytest.raises(ValueError, match="Invalid type for primitivetype"):
        pygeoops.collection_extract(shapely.Point((0, 0)), primitivetype=None)
    with pytest.raises(ValueError, match="Invalid type for primitivetype"):
        pygeoops.collection_extract(shapely.Point((0, 0)), primitivetype="invalid")


def test_empty():
    assert pygeoops.empty(None) is None
    assert pygeoops.empty(1) == shapely.Point()
    assert pygeoops.empty(2) == shapely.LineString()
    assert pygeoops.empty(3) == shapely.Polygon()
    assert pygeoops.empty(4) == shapely.MultiPoint()
    assert pygeoops.empty(5) == shapely.MultiLineString()
    assert pygeoops.empty(6) == shapely.MultiPolygon()
    assert pygeoops.empty(7) == shapely.GeometryCollection()

    # Special case: shapely.Geometry() does not exist, so also collection
    assert pygeoops.empty(0) == shapely.GeometryCollection()

    with pytest.raises(ValueError, match="-2 is not a valid GeometryType"):
        pygeoops.empty(-2)


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


def test_get_primitivetype_id():
    # Test for one geometry
    assert pygeoops.get_primitivetype_id(shapely.Point()) == 1
    assert pygeoops.get_primitivetype_id(shapely.GeometryCollection()) == 0

    # Test with list of all different types
    input = [
        shapely.Point(),
        shapely.MultiPoint(),
        shapely.LineString(),
        shapely.MultiLineString(),
        shapely.Polygon(),
        shapely.MultiPolygon(),
        shapely.GeometryCollection(),
    ]
    expected = [1, 1, 2, 2, 3, 3, 0]

    result = pygeoops.get_primitivetype_id(input)
    assert result.tolist() == expected


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


def test_subdivide():
    # Test with complex polygon, it should be subdivided!
    # ---------------------------------------------------
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
    poly_divided = pygeoops.subdivide(poly_complex, num_coords_max)
    assert isinstance(poly_divided, np.ndarray)
    assert len(poly_divided) == 4

    # Test with standard polygon, should not be subdivided
    # ----------------------------------------------------
    poly_simple = shapely.Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    num_coords_max = 1000
    poly_divided = pygeoops.subdivide(poly_simple, num_coords_max)
    assert isinstance(poly_divided, np.ndarray)
    assert len(poly_divided) == 1
