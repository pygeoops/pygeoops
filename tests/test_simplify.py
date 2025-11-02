"""
Tests on simplify.
"""

import geopandas as gpd
import numpy as np
import pytest
import shapely
import test_helper

import pygeoops


def test_simplify_basic_lang():
    """
    Some basic tests of simplify. The lang algorithm is used because it is no optional
    dependency.
    """
    # Test LineString, lookahead -1, via geometry
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    geom_simplified = pygeoops.simplify(
        geometry=linestring,
        algorithm="lang",
        tolerance=1,
        lookahead=-1,
    )
    assert isinstance(geom_simplified, shapely.LineString)
    assert len(geom_simplified.coords) < len(linestring.coords)
    assert len(geom_simplified.coords) == 2

    # Test Polygon lookahead -1
    poly = shapely.Polygon(
        shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
        holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )
    geom_simplified = pygeoops.simplify(
        geometry=poly,
        algorithm="lang",
        tolerance=1,
        lookahead=-1,
    )
    assert isinstance(geom_simplified, shapely.Polygon)
    assert geom_simplified.exterior is not None
    assert poly.exterior is not None
    assert len(geom_simplified.exterior.coords) < len(poly.exterior.coords)
    assert len(geom_simplified.exterior.coords) == 5

    # Test Point simplification
    point = shapely.Point((0, 0))
    geom_simplified = pygeoops.simplify(geometry=point, algorithm="lang", tolerance=1)
    assert isinstance(geom_simplified, shapely.Point)
    assert len(geom_simplified.coords) == 1

    # Test MultiPoint simplification
    multipoint = shapely.MultiPoint([(0, 0), (10, 10), (20, 20)])
    geom_simplified = pygeoops.simplify(
        geometry=multipoint, algorithm="lang", tolerance=1
    )
    assert isinstance(geom_simplified, shapely.MultiPoint)
    assert len(geom_simplified.geoms) == 3

    # Test LineString simplification
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    geom_simplified = pygeoops.simplify(
        geometry=linestring, algorithm="lang", tolerance=1
    )
    assert isinstance(geom_simplified, shapely.LineString)
    assert len(geom_simplified.coords) < len(linestring.coords)
    assert len(geom_simplified.coords) == 2

    # Two point -> no simplification
    linestring_2points = shapely.LineString([(0, 0), (20, 20)])
    geom_simplified = pygeoops.simplify(
        geometry=linestring_2points, algorithm="lang", tolerance=1
    )
    assert isinstance(geom_simplified, shapely.LineString)
    assert len(geom_simplified.coords) == 2

    # Test MultiLineString simplification
    multilinestring = shapely.MultiLineString(
        [list(linestring.coords), [(100, 100), (110, 110), (120, 120)]]
    )
    geom_simplified = pygeoops.simplify(
        geometry=multilinestring,
        algorithm="lang",
        tolerance=1,
    )
    assert isinstance(geom_simplified, shapely.MultiLineString)
    assert len(geom_simplified.geoms) == 2
    assert len(geom_simplified.geoms[0].coords) < len(multilinestring.geoms[0].coords)
    assert len(geom_simplified.geoms[0].coords) == 2

    # Test Polygon simplification
    poly = shapely.Polygon(
        shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
        holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )
    geom_simplified = pygeoops.simplify(geometry=poly, algorithm="lang", tolerance=1)
    assert isinstance(geom_simplified, shapely.Polygon)
    assert geom_simplified.exterior is not None
    assert poly.exterior is not None
    assert len(geom_simplified.exterior.coords) < len(poly.exterior.coords)
    assert len(geom_simplified.exterior.coords) == 5

    # Test MultiPolygon simplification
    poly2 = shapely.Polygon(
        shell=[(100, 100), (100, 110), (110, 110), (110, 100), (100, 100)]
    )
    multipoly = shapely.MultiPolygon([poly, poly2])
    geom_simplified = pygeoops.simplify(
        geometry=multipoly, algorithm="lang", tolerance=1
    )
    assert isinstance(geom_simplified, shapely.MultiPolygon)
    assert len(geom_simplified.geoms) == 2
    assert len(geom_simplified.geoms[0].exterior.coords) < len(poly.exterior.coords)
    assert len(geom_simplified.geoms[0].exterior.coords) == 5

    # Test GeometryCollection (as combination of all previous ones) simplification
    geom = shapely.GeometryCollection(
        [point, multipoint, linestring, multilinestring, poly, multipoly]
    )
    geom_simplified = pygeoops.simplify(geometry=geom, algorithm="lang", tolerance=1)
    assert isinstance(geom_simplified, shapely.GeometryCollection)
    assert len(geom_simplified.geoms) == 6


@pytest.mark.parametrize("input_type", ["geoseries", "ndarray", "list"])
def test_simplify_input_geometries(input_type):
    """Test simplify of an array of linestrings."""
    # Prepare test data
    input = [shapely.LineString([(0, 0), (10, 10), (20, 20)])] * 2
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
    result = pygeoops.simplify(geometry=input, algorithm="lang", tolerance=1)

    # Check result
    assert result is not None
    if input_type == "geoseries":
        assert isinstance(result, gpd.GeoSeries)
    else:
        assert isinstance(result, np.ndarray)
    assert len(result) == 2
    for test_idx, simplified_line in enumerate(result):
        assert isinstance(simplified_line, shapely.LineString)
        assert len(simplified_line.coords) < len(input[start_idx + test_idx].coords)
        assert len(simplified_line.coords) == 2


@pytest.mark.parametrize("preserve_common_boundaries", [True, False])
def test_simplify_input_geoseries(preserve_common_boundaries: bool):
    """Test simplify of a geoseries of linestrings."""
    line1 = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    line2 = shapely.LineString([(0, 0), (10, 0), (20, 0)])
    lines = gpd.GeoSeries([line1, line2, line2])
    lines = lines.drop(index=1)
    simplified_lines = pygeoops.simplify(
        geometry=lines,
        algorithm="lang",
        tolerance=1,
        preserve_common_boundaries=preserve_common_boundaries,
    )
    assert simplified_lines is not None
    assert isinstance(simplified_lines, gpd.GeoSeries)
    assert len(simplified_lines) == len(lines)
    assert simplified_lines.index.to_list() == lines.index.to_list()
    for test_idx, simplified_line in simplified_lines.items():
        assert isinstance(simplified_line, shapely.LineString)
        assert len(simplified_line.coords) < len(lines.geometry[test_idx].coords)
        assert len(simplified_line.coords) == 2


def test_simplify_invalid_geometry():
    # Test Polygon simplification, with invalid exterior ring
    poly = shapely.Polygon(
        shell=[(0, 0), (0, 10), (5, 10), (3, 12), (3, 9), (10, 10), (10, 0), (0, 0)],
        holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )
    geom_simplified = pygeoops.simplify(geometry=poly, algorithm="lang", tolerance=1)
    assert isinstance(geom_simplified, shapely.MultiPolygon)
    assert poly.exterior is not None
    assert len(geom_simplified.geoms[0].exterior.coords) < len(poly.exterior.coords)
    assert len(geom_simplified.geoms[0].exterior.coords) == 7
    assert len(geom_simplified.geoms[0].interiors) == len(poly.interiors)

    # Test Polygon simplification, with exterior ring that touches itself
    # due to simplification and after make_valid results in multipolygon of
    # 2 equally large parts (left and right part of M shape).
    poly_m_touch = shapely.Polygon(
        shell=[
            (0, 0),
            (0, 10),
            (5, 5),
            (10, 10),
            (10, 0),
            (8, 0),
            (8, 5),
            (5, 4),
            (2, 5),
            (2, 0),
            (0, 0),
        ]
    )
    geom_simplified = pygeoops.simplify(
        geometry=poly_m_touch,
        algorithm="lang",
        tolerance=1,
    )
    assert geom_simplified is not None
    assert geom_simplified.is_valid
    assert isinstance(geom_simplified, shapely.MultiPolygon)
    assert len(geom_simplified.geoms) == 2
    assert shapely.get_num_coordinates(geom_simplified) < shapely.get_num_coordinates(
        poly
    )

    # Test Polygon simplification, with exterior ring that crosses itself
    # due to simplification and after make_valid results in multipolygon of
    # 3 parts (left, middle and right part of M shape).
    poly_m_cross = shapely.Polygon(
        shell=[
            (0, 0),
            (0, 10),
            (5, 5),
            (10, 10),
            (10, 0),
            (8, 0),
            (8, 5.5),
            (5, 4.5),
            (2, 5.5),
            (2, 0),
            (0, 0),
        ]
    )
    geom_simplified = pygeoops.simplify(
        geometry=poly_m_cross,
        algorithm="lang",
        tolerance=1,
    )
    assert geom_simplified is not None
    assert geom_simplified.is_valid
    assert isinstance(geom_simplified, shapely.MultiPolygon)
    assert len(geom_simplified.geoms) == 3


def test_simplify_invalid_params():
    with pytest.raises(ValueError, match="Unsupported algorithm specified: invalid"):
        pygeoops.simplify(
            geometry=shapely.LineString([(0, 0), (10, 10), (20, 20)]),
            tolerance=1,
            algorithm="invalid_algorithm",
        )

    expected_error = (
        "The combination of preserve_common_boundaries=True and "
        "preserve_topology=False is not supported."
    )
    with pytest.raises(ValueError, match=expected_error):
        pygeoops.simplify(
            geometry=shapely.LineString([(0, 0), (10, 10), (20, 20)]),
            tolerance=1,
            preserve_topology=False,
            preserve_common_boundaries=True,
        )


@pytest.mark.parametrize(
    "algorithm, tolerance", [("lang", 2), ("lang+", 2), ("rdp", 2), ("vw", 15)]
)
def test_simplify_keep_points_on(tmp_path, algorithm, tolerance):
    # Skip test for algorithms that needs simplification lib when it is not available
    if algorithm in ["rdp", "vw"]:
        _ = pytest.importorskip("simplification")

    # Prepare test data
    poly_input = shapely.Polygon(
        shell=[(0, 0), (0, 10), (5, 12), (10, 10), (10, 0), (5, 0), (0, 0)]
    )
    # Create geometry where we want the points kept
    keep_points_on_line = shapely.LineString([(0, 0), (0, 12), (10, 12)])

    # Plot input
    output_path = tmp_path / f"{__name__}_{algorithm}_input.png"
    test_helper.plot([poly_input, keep_points_on_line], output_path)

    # Without keep_points_on
    poly_simpl = pygeoops.simplify(poly_input, algorithm=algorithm, tolerance=tolerance)
    output_path = tmp_path / f"{__name__}_{algorithm}_simpl.png"
    test_helper.plot([poly_simpl], output_path)

    assert len(poly_simpl.exterior.coords) == len(poly_input.exterior.coords) - 2
    assert poly_simpl.area < poly_input.area

    # With keep_points_on
    poly_simpl_keep = pygeoops.simplify(
        poly_input,
        algorithm=algorithm,
        tolerance=tolerance,
        keep_points_on=keep_points_on_line,
    )
    output_path = tmp_path / f"{__name__}_{algorithm}_simpl_keep.png"
    test_helper.plot([poly_simpl_keep], output_path)

    assert len(poly_simpl_keep.exterior.coords) == len(poly_input.exterior.coords) - 1
    assert poly_simpl_keep.area == poly_input.area


@pytest.mark.parametrize("algorithm", ["lang", "lang+", "rdp", "vw"])
def test_simplify_ndarray_0dim(algorithm):
    # Skip test for algorithms that needs simplification lib when it is not available
    if algorithm in ["rdp", "vw"]:
        _ = pytest.importorskip("simplification")

    # Prepare test data
    poly_input = shapely.Polygon(
        shell=[(0, 0), (0, 10), (5, 12), (10, 10), (10, 0), (5, 0), (0, 0)]
    )
    expected = pygeoops.simplify(poly_input, 1, algorithm=algorithm)

    # Test simplify
    result = pygeoops.simplify(np.array(poly_input), 1, algorithm=algorithm)
    assert result == expected


def test_simplify_None():
    # Test simplify on None geometry
    result = pygeoops.simplify(None, 1)
    assert result is None

    # Test simplify on None geometry list
    result = pygeoops.simplify([None], 1)
    assert result == [None]


@pytest.mark.parametrize(
    "algorithm, tolerance", [("lang", 10), ("lang+", 10), ("vw", 50)]
)
def test_simplify_preservetopology(algorithm, tolerance):
    # Skip test for algorithms that needs simplification lib when it is not available
    if algorithm in ["rdp", "vw"]:
        _ = pytest.importorskip("simplification")

    # Test Polygon lookahead -1
    poly = shapely.Polygon(
        shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
        holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )

    # If preserve_topology True, the original polygon is returned
    geom_simplified = pygeoops.simplify(
        geometry=poly,
        algorithm=algorithm,
        tolerance=tolerance,
        preserve_topology=True,
    )
    assert isinstance(geom_simplified, shapely.Polygon)
    assert poly.equals(geom_simplified) is True

    # If preserve_topology False, the polygon becomes None
    geom_simplified = pygeoops.simplify(
        geometry=poly,
        algorithm=algorithm,
        tolerance=tolerance,
        preserve_topology=False,
    )
    assert geom_simplified is None
