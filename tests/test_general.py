"""
Tests for functionalities in _general.
"""

import geopandas as gpd
import numpy as np
import pytest
import shapely
from shapely import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

import pygeoops
import pygeoops._general
from pygeoops import PrimitiveType

MULTIPOLY_INVALID_1_COLLAPSING_LINE = MultiPolygon(
    [
        Polygon([(0, 0), (0, 10), (10, 0), (10, 10), (0, 0)]),
        Polygon([(1, 1), (2, 1), (3, 1)]),
    ]
)
LINESTRING_INVALID_2_COLLAPSING_POINT = MultiLineString(
    [
        LineString([(0, 0), (5, 0), (10, 0)]),
        LineString([(1, 1), (1, 1)]),
    ]
)


def test_collect():
    # Test dealing with None/empty input
    # ----------------------------------
    assert pygeoops.collect(None) is None
    assert pygeoops.collect([None]) is None
    # Empty geometries are treated as None as well
    assert pygeoops.collect([None, Polygon(), None, Polygon()]) is None

    # Test points
    # -----------
    point = Point((0, 0))
    assert pygeoops.collect(point) == point
    assert pygeoops.collect([point]) == point
    assert pygeoops.collect([point, point]) == MultiPoint([(0, 0), (0, 0)])

    # Test linestrings
    # ----------------
    line = LineString([(0, 0), (0, 1)])
    assert pygeoops.collect(line) == line
    assert pygeoops.collect([line]) == line
    assert pygeoops.collect([line, line]) == MultiLineString([line, line])

    # Test polygons
    # -------------
    poly01 = shapely.box(0, 0, 1, 1)
    poly23 = shapely.box(2, 0, 3, 1)
    poly34 = shapely.box(3, 0, 4, 1)
    poly45 = shapely.box(4, 0, 5, 1)
    multipoly = MultiPolygon([poly23, poly45])
    assert pygeoops.collect(poly01) == poly01
    assert pygeoops.collect([poly01]) == poly01
    assert pygeoops.collect([poly23, poly45]) == multipoly
    # Adjacent polygons: would create invalid multipolygon so becomes GeometryCollection
    assert pygeoops.collect([poly34, poly45]) == GeometryCollection([poly34, poly45])

    # Test geometrycollection
    # -----------------------
    geometrycoll = GeometryCollection([point, line, poly01])
    assert pygeoops.collect(geometrycoll) == geometrycoll
    assert pygeoops.collect([geometrycoll]) == geometrycoll
    assert pygeoops.collect([point, line, poly01]) == geometrycoll
    assert pygeoops.collect([geometrycoll, line]) == GeometryCollection(
        [geometrycoll, line]
    )
    assert pygeoops.collect([poly01, multipoly]) == GeometryCollection(
        [poly01, multipoly]
    )

    # Test arraylike input
    # --------------------
    assert pygeoops.collect(gpd.GeoSeries([point, line, poly01])) == geometrycoll
    assert pygeoops.collect(np.array([point, line, poly01])) == geometrycoll

    # Test arraylike input, 0 dimension
    # ---------------------------------
    # Single geometry in ndarray -> 0 dim array: shapely functions return simple result
    assert pygeoops.collect(np.array(point)) == point
    assert pygeoops.collect(np.array(line)) == line
    assert pygeoops.collect(np.array(multipoly)) == multipoly


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
    point = Point((0, 0))
    multipoint = MultiPoint([point, point])
    assert pygeoops.collection_extract(point, 1) == point
    assert pygeoops.collection_extract(multipoint, 1) == multipoint
    assert pygeoops.collection_extract(multipoint, 2) is None

    # Test dealing with 0 dim array/scalar
    # ------------------------------------
    assert pygeoops.collection_extract(np.array(point), 1) == point

    # Test dealing with mixed geometries
    # ----------------------------------
    line = LineString([(0, 0), (0, 1)])
    poly1 = shapely.box(0, 0, 1, 1)
    poly2 = shapely.box(2, 0, 3, 1)
    poly3 = shapely.box(4, 0, 5, 1)
    multipoly = MultiPolygon([poly2, poly3])
    geometrycoll = GeometryCollection([point, line, poly1, multipoly])
    assert pygeoops.collection_extract(geometrycoll, 1) == point
    assert pygeoops.collection_extract(geometrycoll, PrimitiveType.POINT) == point
    assert pygeoops.collection_extract(geometrycoll, 2) == line
    assert pygeoops.collection_extract(geometrycoll, PrimitiveType.LINESTRING) == line
    assert pygeoops.collection_extract(geometrycoll, 3) == GeometryCollection(
        [poly1, multipoly]
    )
    assert pygeoops.collection_extract(
        geometrycoll, PrimitiveType.POLYGON
    ) == GeometryCollection([poly1, multipoly])
    assert pygeoops.collection_extract(geometrycoll, 0) == geometrycoll

    # Test dealing with deeper nested geometries
    # ------------------------------------------
    assert pygeoops.collection_extract(
        GeometryCollection(geometrycoll), 0
    ) == GeometryCollection(geometrycoll)

    # Test dealing with single element ndarray (0 dimension)
    # ------------------------------------------------------
    assert pygeoops.collection_extract(np.array(point), 1) == point
    assert pygeoops.collection_extract(np.array(multipoint), 1) == multipoint
    assert pygeoops.collection_extract(np.array(multipoint), 2) is None

    assert pygeoops.collection_extract(np.array(geometrycoll), 1) == point
    assert (
        pygeoops.collection_extract(np.array(geometrycoll), PrimitiveType.POINT)
        == point
    )


@pytest.mark.parametrize("input_type", ["geoseries", "ndarray", "list"])
def test_collection_extract_geometries(input_type):
    """
    Test collection_extract with several geometries as input and extracting only points.
    """
    # Prepare test data
    point = Point((0, 0))
    multipoint = MultiPoint([point, point])
    line = LineString([(0, 0), (0, 1)])
    poly1 = shapely.box(0, 0, 1, 1)
    poly2 = shapely.box(2, 0, 3, 1)
    poly3 = shapely.box(4, 0, 5, 1)
    multipoly = MultiPolygon([poly2, poly3])
    geometrycoll = GeometryCollection([point, line, poly1, multipoly])
    input = [point, multipoint, line, poly1, multipoly, geometrycoll]
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
    assert len(result) == len(input)
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


def test_collection_extract_geometries_primitivetypes():
    """
    Test collection_extract on geometrycollections as input and extract different
    primitive types.
    """
    # Prepare test data
    point = Point((0, 0))
    line = LineString([(0, 0), (0, 1)])
    poly1 = shapely.box(0, 0, 1, 1)
    poly2 = shapely.box(2, 0, 3, 1)
    poly3 = shapely.box(4, 0, 5, 1)
    multipoly = MultiPolygon([poly2, poly3])
    geometrycoll = GeometryCollection([point, line, poly1, multipoly])
    input = [geometrycoll] * 4
    primitivetypes = [0, 1, 2, 3]

    # Run test
    result = pygeoops.collection_extract(input, primitivetype=primitivetypes)

    # Check result
    assert result is not None
    assert result[0] == geometrycoll
    assert result[1] == point
    assert result[2] == line
    assert isinstance(result[3], GeometryCollection)
    assert len(result[3].geoms) == 2
    assert result[3].geoms[0] == poly1
    assert result[3].geoms[1] == multipoly


def test_collection_extract_invalid_params():
    with pytest.raises(ValueError, match="Invalid value for primitivetype: 5"):
        pygeoops.collection_extract(Point((0, 0)), primitivetype=5)
    with pytest.raises(ValueError, match="Invalid value for primitivetype: -5"):
        pygeoops.collection_extract(Point((0, 0)), primitivetype=-5)
    with pytest.raises(ValueError, match="Invalid value for primitivetype: None"):
        pygeoops.collection_extract(Point((0, 0)), primitivetype=None)
    with pytest.raises(ValueError, match="Invalid type for primitivetype"):
        pygeoops.collection_extract(Point((0, 0)), primitivetype="invalid")

    # Test lists of different length for geometries vs. primitivetypes
    with pytest.raises(
        ValueError,
        match="geometry and primitivetype are arraylike, so len must be equal",
    ):
        pygeoops.collection_extract([Point((0, 0))], primitivetype=[1, 2])
    with pytest.raises(
        ValueError, match="single geometry passed, but primitivetype is arraylike"
    ):
        pygeoops.collection_extract(Point((0, 0)), primitivetype=[1, 2])


@pytest.mark.parametrize("test", ["adjacent", "disjoint"])
def test_collection_extract_polygons(test):
    # Create geometrycollection with two polygons that are right next to each other
    box0_4 = shapely.box(0, 0, 4, 5)
    box0_5 = shapely.box(0, 0, 5, 5)
    box5_10 = shapely.box(5, 0, 10, 5)

    if test == "adjacent":
        collection_poly = GeometryCollection([box0_5, box5_10])

        # Result should stay a GeometryCollection(, because a multipolygon where outer
        # rings have common border is not valid.
        expected_result = collection_poly

    elif test == "disjoint":
        collection_poly = GeometryCollection([box0_4, box5_10])

        # Result should be a multipolygon, because the polygons aren't adjacent
        expected_result = MultiPolygon([box0_4, box5_10])

    # Extract polygons
    result = pygeoops.collection_extract(collection_poly, primitivetype=3)

    assert result == expected_result


def test_empty():
    assert pygeoops.empty(None) is None
    assert pygeoops.empty(1) == Point()
    assert pygeoops.empty(2) == LineString()
    assert pygeoops.empty(3) == Polygon()
    assert pygeoops.empty(4) == MultiPoint()
    assert pygeoops.empty(5) == MultiLineString()
    assert pygeoops.empty(6) == MultiPolygon()
    assert pygeoops.empty(7) == GeometryCollection()

    # Special case: shapely.Geometry() does not exist, so also collection
    assert pygeoops.empty(0) == GeometryCollection()

    with pytest.raises(ValueError, match="-2 is not a valid GeometryType"):
        pygeoops.empty(-2)


@pytest.mark.filterwarnings("ignore:Deprecated")
def test_explode():
    # Test dealing with None/empty input
    # ----------------------------------
    assert pygeoops.explode(None) is None

    # Test dealing with points
    # ------------------------
    point = Point((0, 0))
    multipoint = MultiPoint([point, point])
    assert pygeoops.explode(point).tolist() == [point]
    assert pygeoops.explode(multipoint).tolist() == [point, point]

    # Test dealing with linestrings
    # -----------------------------
    line = LineString([(0, 0), (0, 1)])
    multiline = MultiLineString([line, line])
    assert pygeoops.explode(line).tolist() == [line]
    assert pygeoops.explode(multiline).tolist() == [line, line]

    # Test dealing with Polygons
    # --------------------------
    poly = Polygon([(0, 0), (0, 1), (0, 0)])
    multipoly = MultiPolygon([poly, poly])
    assert pygeoops.explode(poly).tolist() == [poly]
    assert pygeoops.explode(multipoly).tolist() == [poly, poly]

    # Test geometrycollection
    # -----------------------
    geometrycoll = GeometryCollection([point, line, poly])
    assert pygeoops.explode(geometrycoll).tolist() == [point, line, poly]


@pytest.mark.parametrize(
    "geometry, expected",
    [
        (None, "None"),
        (Point((0, 0)), "POINT(0.0 0.0)"),
        (MultiPoint([(0, 0), (1, 1)]), "MULTIPOINT(0.0 0.0, ...)"),
        (LineString([(0, 0), (0, 1)]), "LINESTRING(0.0 0.0, ...)"),
        (MultiLineString([[(0, 0), (0, 1)]]), "MULTILINESTRING((0.0 0.0, ...)"),
        (Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]), "POLYGON(0.0 0.0, ...)"),
        (
            MultiPolygon([Polygon([(0.01, 0.0), (0.02, 0.0), (0.02, 0.01)])]),
            "MULTIPOLYGON((0.01 0.0, ...)",
        ),
        (
            GeometryCollection([Point((0, 0))]),
            "GEOMETRYCOLLECTION(POINT(0.0 0.0))",
        ),
        (
            GeometryCollection([Point((0, 0)), Point((1, 1))]),
            "GEOMETRYCOLLECTION(POINT(0.0 0.0), ...)",
        ),
        (
            GeometryCollection([Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])]),
            "GEOMETRYCOLLECTION(POLYGON(0.0 0.0, ...)",
        ),
        (
            GeometryCollection(
                [GeometryCollection([MultiLineString([[(0, 0), (0, 1)]])])]
            ),
            "GEOMETRYCOLLECTION(GEOMETRYCOLLECTION(MULTILINESTRING((0.0 0.0, ...)",
        ),
    ],
)
def test_format_short(geometry, expected):
    """Test the format_short function."""
    # Test with None input
    assert pygeoops.format_short(geometry) == expected


def test_get_parts_recursive():
    # Test None input
    assert pygeoops.get_parts_recursive(None) is None

    # Test simple geometries
    point = Point((0, 0))
    line = LineString([(0, 0), (0, 1)])
    poly = shapely.box(0, 0, 1, 1)
    assert pygeoops.get_parts_recursive(point) == [point]
    assert pygeoops.get_parts_recursive(line) == [line]
    assert pygeoops.get_parts_recursive(poly) == [poly]

    # Test multi geometries
    multipoint = MultiPoint([point, point])
    multiline = MultiLineString([line, line])
    multipoly = MultiPolygon([poly, poly])
    assert pygeoops.get_parts_recursive(multipoint).tolist() == [point, point]
    assert pygeoops.get_parts_recursive(multiline).tolist() == [line, line]
    assert pygeoops.get_parts_recursive(multipoly).tolist() == [poly, poly]

    # Test geometrycollection
    geometrycoll = GeometryCollection([point, line, poly])
    assert pygeoops.get_parts_recursive(geometrycoll).tolist() == [point, line, poly]

    # Test deeper nested geometrycollection
    deep_geometrycoll = GeometryCollection(
        [GeometryCollection([multipoint, multiline]), multipoly]
    )
    expected_parts = [point, point, line, line, poly, poly]
    assert pygeoops.get_parts_recursive(deep_geometrycoll).tolist() == expected_parts


@pytest.mark.parametrize(
    "test_id, input, expected_id",
    [
        (1, Point(), 1),
        (2, GeometryCollection(), 0),
        (3, np.array(Point()), 1),
        (4, np.array(GeometryCollection()), 0),
    ],
)
def test_get_primitivetype_id(test_id, input, expected_id):
    # Test for one geometry
    assert pygeoops.get_primitivetype_id(input) == expected_id


def test_get_primitivetype_ids():
    # Test with list of all different types
    input = [
        Point(),
        MultiPoint(),
        LineString(),
        MultiLineString(),
        Polygon(),
        MultiPolygon(),
        GeometryCollection(),
    ]
    expected = [1, 1, 2, 2, 3, 3, 0]

    result = pygeoops.get_primitivetype_id(input)
    assert isinstance(result, np.ndarray)
    assert result.tolist() == expected


@pytest.mark.parametrize(
    "test_id, input, expected",
    [
        (1, 1, False),
        (2, [1], True),
        (3, np.array(1), True),
        (4, np.array([1, 2]), True),
        (5, "abc", False),
        (6, ["abc", "def"], True),
    ],
)
def test_is_iterable_arraylike(test_id, input, expected):
    assert pygeoops._general._is_arraylike(input) is expected


@pytest.mark.parametrize("only_if_invalid", [True, False])
@pytest.mark.parametrize(
    "geometry, keep_collapsed, exp_geometrytype",
    [
        (MULTIPOLY_INVALID_1_COLLAPSING_LINE, True, GeometryCollection),
        (MULTIPOLY_INVALID_1_COLLAPSING_LINE, False, MultiPolygon),
        (
            np.array(MULTIPOLY_INVALID_1_COLLAPSING_LINE),
            True,
            GeometryCollection,
        ),
        (np.array(MULTIPOLY_INVALID_1_COLLAPSING_LINE), False, MultiPolygon),
        (None, False, None),
        (np.array(None), True, None),
        (shapely.box(0, 0, 5, 5), False, Polygon),
        (np.array(shapely.box(0, 0, 5, 5)), True, Polygon),
    ],
)
def test_makevalid_keep_collapsed(
    geometry, keep_collapsed, only_if_invalid, exp_geometrytype
):
    # Test
    result = pygeoops.make_valid(
        geometry, keep_collapsed=keep_collapsed, only_if_invalid=only_if_invalid
    )

    # Check result
    if exp_geometrytype is None:
        assert result is None
    else:
        assert result is not None
        assert isinstance(result, exp_geometrytype)


@pytest.mark.parametrize("input_type", ["geoseries", "ndarray", "list"])
@pytest.mark.parametrize("only_if_invalid", [True, False])
@pytest.mark.parametrize(
    "input, keep_collapsed, exp_geometrytype",
    [
        (
            [
                MULTIPOLY_INVALID_1_COLLAPSING_LINE,
                LINESTRING_INVALID_2_COLLAPSING_POINT,
            ],
            True,
            [GeometryCollection, GeometryCollection],
        ),
        (
            [
                MULTIPOLY_INVALID_1_COLLAPSING_LINE,
                LINESTRING_INVALID_2_COLLAPSING_POINT,
            ],
            False,
            [MultiPolygon, LineString],
        ),
        (
            [
                shapely.box(0, 0, 1, 1),
                shapely.box(5, 0, 6, 1),
            ],
            False,
            [Polygon, Polygon],
        ),
    ],
)
def test_makevalid_multi(
    input, input_type, keep_collapsed, only_if_invalid, exp_geometrytype
):
    # Prepare test data
    start_idx = 0
    if input_type == "list":
        pass
    elif input_type == "geoseries":
        # For geoseries, also check if the indexers are retained!
        start_idx = 5
        input = gpd.GeoSeries(
            input,
            index=[index + start_idx for index in range(len(input))],
        )
    elif input_type == "ndarray":
        input = np.array(input)
    else:
        raise ValueError(f"unsupported input_type: {input_type}")

    result = pygeoops.make_valid(
        input, keep_collapsed=keep_collapsed, only_if_invalid=only_if_invalid
    )

    # Check result
    assert result is not None

    if input_type == "geoseries":
        assert isinstance(result, gpd.GeoSeries)
    elif input_type:
        assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    for idx in range(len(input)):
        assert isinstance(result[idx + start_idx], exp_geometrytype[idx])


def test_remove_inner_rings():
    # Test with None input
    assert pygeoops.remove_inner_rings(None, min_area_to_keep=1, crs=None) is None

    # Apply to single Polygon, with area tolerance smaller than holes
    polygon_removerings_withholes = Polygon(
        shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
        holes=[
            [(2, 2), (2, 4), (4, 4), (4, 2), (2, 2)],
            [(5, 5), (5, 6), (7, 6), (7, 5), (5, 5)],
        ],
    )
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_withholes, min_area_to_keep=1, crs=None
    )
    assert isinstance(poly_result, Polygon)
    assert len(poly_result.interiors) == 2

    # Apply to single Polygon, with area tolerance smaller than holes and passed as a
    # 0 dimension ndarray
    poly_result = pygeoops.remove_inner_rings(
        np.array(polygon_removerings_withholes), min_area_to_keep=1, crs=None
    )
    assert isinstance(poly_result, Polygon)
    assert len(poly_result.interiors) == 2

    # Apply to single Polygon, with area tolerance between
    # smallest hole (= 2m²) and largest (= 4m²)
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_withholes, min_area_to_keep=3, crs="epsg:31370"
    )
    assert isinstance(poly_result, Polygon)
    assert len(poly_result.interiors) == 1

    # Apply to single polygon and remove all holes
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_withholes, min_area_to_keep=0, crs=None
    )
    assert isinstance(poly_result, Polygon)
    assert len(poly_result.interiors) == 0
    polygon_removerings_noholes = Polygon(
        shell=[(100, 100), (100, 110), (110, 110), (110, 100), (100, 100)]
    )
    poly_result = pygeoops.remove_inner_rings(
        polygon_removerings_noholes, min_area_to_keep=0, crs=None
    )
    assert isinstance(poly_result, Polygon)
    assert len(poly_result.interiors) == 0

    # Apply to MultiPolygon, with area tolerance between
    # smallest hole (= 2m²) and largest (= 4m²)
    multipoly_removerings = MultiPolygon(
        [polygon_removerings_withholes, polygon_removerings_noholes]
    )
    poly_result = pygeoops.remove_inner_rings(
        multipoly_removerings, min_area_to_keep=3, crs=None
    )
    assert isinstance(poly_result, MultiPolygon)
    interiors = poly_result.geoms[0].interiors  # pyright: ignore[reportOptionalMemberAccess]
    assert len(interiors) == 1


def test_remove_inner_rings_invalid_input():
    with pytest.raises(ValueError, match="remove_inner_rings impossible on LineString"):
        pygeoops.remove_inner_rings(
            LineString([(0, 0), (0, 1)]), min_area_to_keep=1, crs=None
        )


def test_subdivide():
    # Prepare a complex polygon to test with
    poly_size = 1000
    poly_distance = 50
    lines = []
    for off in range(0, poly_size, poly_distance):
        lines.append(LineString([(off, 0), (off, poly_size)]))
        lines.append(LineString([(0, off), (poly_size, off)]))

    poly_complex = shapely.unary_union(MultiLineString(lines).buffer(2))
    assert len(shapely.get_parts(poly_complex)) == 1
    num_coordinates = shapely.get_num_coordinates(poly_complex)
    assert num_coordinates == 3258

    # Test with complex polygon, it should be subdivided!
    num_coords_max = 1000
    poly_divided = pygeoops.subdivide(poly_complex, num_coords_max)
    assert isinstance(poly_divided, np.ndarray)
    assert len(poly_divided) == 4

    # Test with complex polygon passed on as 0 dim ndarray, it should be subdivided!
    poly_divided = pygeoops.subdivide(np.array(poly_complex), num_coords_max)
    assert isinstance(poly_divided, np.ndarray)
    assert len(poly_divided) == 4

    # Test with complex polygon, but num_coords_max = 0 -> not subdivided!
    poly_divided = pygeoops.subdivide(poly_complex, 0)
    assert isinstance(poly_divided, np.ndarray)
    assert len(poly_divided) == 1

    # Test with standard polygon, should not be subdivided
    poly_simple = Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
    num_coords_max = 1000
    poly_divided = pygeoops.subdivide(poly_simple, num_coords_max)
    assert isinstance(poly_divided, np.ndarray)
    assert len(poly_divided) == 1
