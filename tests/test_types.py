# -*- coding: utf-8 -*-
"""
Tests on the types defined in types.py.
"""

import pytest

from pygeoops import GeometryType, PrimitiveType


def test_geometrytype():
    # Creating a GeometryType from None is invalid
    with pytest.raises(ValueError, match="None is not a valid GeometryType"):
        _ = GeometryType(None)

    # Create different types of Geometrytype
    assert GeometryType(3) is GeometryType.POLYGON
    assert GeometryType("PoLyGoN") is GeometryType.POLYGON
    assert GeometryType("PoLyGoN") is GeometryType.POLYGON
    assert GeometryType(GeometryType.POLYGON) is GeometryType.POLYGON


def test_geometrytype_is_multitype():
    # Test is_multitype
    assert not GeometryType.POLYGON.is_multitype
    assert GeometryType.MULTIPOLYGON.is_multitype
    assert not GeometryType.LINESTRING.is_multitype
    assert GeometryType.MULTILINESTRING.is_multitype
    assert not GeometryType.POINT.is_multitype
    assert GeometryType.MULTIPOINT.is_multitype
    assert GeometryType.GEOMETRY.is_multitype
    assert GeometryType.GEOMETRYCOLLECTION.is_multitype


def test_geometrytype_name_camelcase():
    # Test to_singletype
    assert GeometryType.POLYGON.name_camelcase == "Polygon"
    assert GeometryType.MULTIPOLYGON.name_camelcase == "MultiPolygon"
    assert GeometryType.LINESTRING.name_camelcase == "LineString"
    assert GeometryType.MULTILINESTRING.name_camelcase == "MultiLineString"
    assert GeometryType.POINT.name_camelcase == "Point"
    assert GeometryType.MULTIPOINT.name_camelcase == "MultiPoint"
    assert GeometryType.GEOMETRY.name_camelcase == "Geometry"
    assert GeometryType.GEOMETRYCOLLECTION.name_camelcase == "GeometryCollection"


def test_geometrytype_to_primitivetype():
    # Test to_primitivetype
    assert GeometryType.POLYGON.to_primitivetype is PrimitiveType.POLYGON
    assert GeometryType.MULTIPOLYGON.to_primitivetype is PrimitiveType.POLYGON
    assert GeometryType.LINESTRING.to_primitivetype is PrimitiveType.LINESTRING
    assert GeometryType.MULTILINESTRING.to_primitivetype is PrimitiveType.LINESTRING
    assert GeometryType.POINT.to_primitivetype is PrimitiveType.POINT
    assert GeometryType.MULTIPOINT.to_primitivetype is PrimitiveType.POINT

    # A geometry collection doesn't have a primitive type
    with pytest.raises(
        Exception, match="GeometryType.GEOMETRYCOLLECTION doesn't have a primitive type"
    ):
        GeometryType.GEOMETRYCOLLECTION.to_primitivetype


def test_geometrytype_to_multitype():
    # Test to_multitype
    assert GeometryType.POLYGON.to_multitype is GeometryType.MULTIPOLYGON
    assert GeometryType.MULTIPOLYGON.to_multitype is GeometryType.MULTIPOLYGON
    assert GeometryType.LINESTRING.to_multitype is GeometryType.MULTILINESTRING
    assert GeometryType.MULTILINESTRING.to_multitype is GeometryType.MULTILINESTRING
    assert GeometryType.POINT.to_multitype is GeometryType.MULTIPOINT
    assert GeometryType.MULTIPOINT.to_multitype is GeometryType.MULTIPOINT
    assert GeometryType.GEOMETRY.to_multitype is GeometryType.GEOMETRY
    assert (
        GeometryType.GEOMETRYCOLLECTION.to_multitype is GeometryType.GEOMETRYCOLLECTION
    )


def test_geometrytype_to_singletype():
    # Test to_singletype
    assert GeometryType.POLYGON.to_singletype is GeometryType.POLYGON
    assert GeometryType.MULTIPOLYGON.to_singletype is GeometryType.POLYGON
    assert GeometryType.LINESTRING.to_singletype is GeometryType.LINESTRING
    assert GeometryType.MULTILINESTRING.to_singletype is GeometryType.LINESTRING
    assert GeometryType.POINT.to_singletype is GeometryType.POINT
    assert GeometryType.MULTIPOINT.to_singletype is GeometryType.POINT
    assert GeometryType.GEOMETRY.to_singletype is GeometryType.GEOMETRY
    assert GeometryType.GEOMETRYCOLLECTION.to_singletype is GeometryType.GEOMETRY


def test_primitivetype():
    assert PrimitiveType(3) is PrimitiveType.POLYGON
    assert PrimitiveType(2) is PrimitiveType.LINESTRING
    assert PrimitiveType(1) is PrimitiveType.POINT
    assert PrimitiveType("PoLyGoN") is PrimitiveType.POLYGON
    assert PrimitiveType(PrimitiveType.POLYGON) is PrimitiveType.POLYGON


def test_primitivetype_to_multitype():
    assert PrimitiveType.POLYGON.to_multitype is GeometryType.MULTIPOLYGON
    assert PrimitiveType.LINESTRING.to_multitype is GeometryType.MULTILINESTRING
    assert PrimitiveType.POINT.to_multitype is GeometryType.MULTIPOINT


def test_primitivetype_to_singletype():
    assert PrimitiveType.POLYGON.to_singletype is GeometryType.POLYGON
    assert PrimitiveType.LINESTRING.to_singletype is GeometryType.LINESTRING
    assert PrimitiveType.POINT.to_singletype is GeometryType.POINT
