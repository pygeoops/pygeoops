# -*- coding: utf-8 -*-
"""
Tests on simplify.
"""

import pytest
import shapely

import pygeoops
import test_helper


def test_simplify_arr():
    """Test simplify of an array of linestrings."""
    linestrings = [shapely.LineString([(0, 0), (10, 10), (20, 20)])] * 2
    simplified_lines = pygeoops.simplify(
        geometry=linestrings, algorithm="lang", tolerance=1
    )
    assert simplified_lines is not None
    assert len(simplified_lines) == 2
    for test_idx, simplified_line in enumerate(simplified_lines):
        assert isinstance(simplified_line, shapely.LineString)
        assert len(simplified_line.coords) < len(linestrings[test_idx].coords)
        assert len(simplified_line.coords) == 2


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
    with pytest.raises(ValueError, match="Unsupported algorythm specified: invalid!"):
        pygeoops.simplify(
            geometry=shapely.LineString([(0, 0), (10, 10), (20, 20)]),
            tolerance=1,
            algorithm="invalid!",
        )


@pytest.mark.parametrize("algorithm, tolerance", [("lang", 2), ("rdp", 2), ("vw", 15)])
def test_simplify_keep_points_on(tmp_path, algorithm, tolerance):
    # Skip test if simplification is not available
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


def test_simplify_None():
    # Test simplify on None geometry
    result = pygeoops.simplify(None, 1)
    assert result is None

    # Test simplify on None geometry list
    result = pygeoops.simplify([None], 1)
    assert result == [None]


def test_simplify_preservetopology_lang():
    # Test Polygon lookahead -1
    poly = shapely.Polygon(
        shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
        holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )
    # If preserve_topology True, the original polygon is returned...
    geom_simplified = pygeoops.simplify(
        geometry=poly,
        algorithm="lang",
        tolerance=10,
        preserve_topology=True,
        lookahead=-1,
    )
    assert isinstance(geom_simplified, shapely.Polygon)
    assert poly.equals(geom_simplified) is True

    # If preserve_topology True, the original polygon is returned...
    geom_simplified = pygeoops.simplify(
        geometry=poly,
        algorithm="lang",
        tolerance=10,
        preserve_topology=False,
        lookahead=-1,
    )
    assert geom_simplified is None
