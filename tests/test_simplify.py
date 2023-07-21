# -*- coding: utf-8 -*-
"""
Tests on simplify.
"""

import sys

import geopandas as gpd
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
    assert pygeoops.numberpoints(geom_simplified) < pygeoops.numberpoints(poly)

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


def test_simplify_keep_points_on_lang(tmp_path):
    # First init some stuff
    input_path = test_helper.get_testfile("polygon-simplify-onborder-testcase")
    input_gdf = gpd.read_file(input_path)

    # Create geometry where we want the points kept
    grid_gdf = pygeoops.create_grid(
        total_bounds=(
            210431.875 - 1000,
            176640.125 - 1000,
            210431.875 + 1000,
            176640.125 + 1000,
        ),
        nb_columns=2,
        nb_rows=2,
        crs="epsg:31370",
    )
    grid_gdf.to_file(tmp_path / "grid.gpkg")
    grid_coords = [tile.exterior.coords for tile in grid_gdf.geometry]
    grid_lines_geom = shapely.MultiLineString(grid_coords)

    # Test lang
    # Without keep_points_on, the following point that is on the test data +
    # on the grid is removed by lang
    point_on_input_and_border = shapely.Point(210431.875, 176606.125)
    tolerance_lang = 0.25
    step_lang = 8

    # Determine the number of intersects with the input test data
    nb_intersects_with_input = len(
        input_gdf[input_gdf.intersects(point_on_input_and_border)]
    )
    assert nb_intersects_with_input > 0
    # Test if intersects > 0
    assert len(input_gdf[grid_gdf.intersects(point_on_input_and_border)]) > 0

    # Without keep_points_on the number of intersections changes
    simplified_gdf = input_gdf.copy()
    # assert to evade pyLance warning
    assert isinstance(simplified_gdf, gpd.GeoDataFrame)
    simplified_gdf.geometry = input_gdf.geometry.apply(
        lambda geom: pygeoops.simplify(
            geom,
            algorithm="lang",
            tolerance=tolerance_lang,
            lookahead=step_lang,
        )
    )
    simplified_gdf.to_file(
        tmp_path / f"simplified_lang;{tolerance_lang};{step_lang}.gpkg"
    )
    assert (
        len(simplified_gdf[simplified_gdf.intersects(point_on_input_and_border)])
        != nb_intersects_with_input
    )

    # With keep_points_on specified, the number of intersections stays the same
    simplified_gdf = input_gdf.copy()
    # assert to evade pyLance warning
    assert isinstance(simplified_gdf, gpd.GeoDataFrame)
    simplified_gdf.geometry = input_gdf.geometry.apply(
        lambda geom: pygeoops.simplify(
            geom,
            algorithm="lang",
            tolerance=tolerance_lang,
            lookahead=step_lang,
            keep_points_on=grid_lines_geom,
        )
    )
    output_path = (
        tmp_path / f"simplified_lang;{tolerance_lang};{step_lang}_keep_points_on.gpkg"
    )
    simplified_gdf.to_file(output_path)
    assert (
        len(simplified_gdf[simplified_gdf.intersects(point_on_input_and_border)])
        == nb_intersects_with_input
    )


def test_simplify_keep_points_on_rdp(tmp_path):
    # Skip test if simplification is not available
    _ = pytest.importorskip("simplification")

    # First init some stuff
    input_path = test_helper.get_testfile("polygon-simplify-onborder-testcase")
    input_gdf = gpd.read_file(input_path)

    # Create geometry where we want the points kept
    grid_gdf = pygeoops.create_grid(
        total_bounds=(
            210431.875 - 1000,
            176640.125 - 1000,
            210431.875 + 1000,
            176640.125 + 1000,
        ),
        nb_columns=2,
        nb_rows=2,
        crs="epsg:31370",
    )
    grid_gdf.to_file(tmp_path / "grid.gpkg")
    grid_coords = [tile.exterior.coords for tile in grid_gdf.geometry]
    grid_lines_geom = shapely.MultiLineString(grid_coords)

    # Test rdp (ramer–douglas–peucker)
    # Without keep_points_on, the following point that is on the test data +
    # on the grid is removed by rdp
    point_on_input_and_border = shapely.Point(210431.875, 176599.375)
    tolerance_rdp = 0.5

    # Determine the number of intersects with the input test data
    nb_intersects_with_input = len(
        input_gdf[input_gdf.intersects(point_on_input_and_border)]
    )
    assert nb_intersects_with_input > 0
    # Test if intersects > 0
    assert len(input_gdf[grid_gdf.intersects(point_on_input_and_border)]) > 0

    # Without keep_points_on the number of intersections changes
    simplified_gdf = input_gdf.copy()
    # assert to evade pyLance warning
    assert isinstance(simplified_gdf, gpd.GeoDataFrame)
    simplified_gdf.geometry = input_gdf.geometry.apply(
        lambda geom: pygeoops.simplify(
            geom,
            algorithm="rdp",
            tolerance=tolerance_rdp,
        )
    )
    simplified_gdf.to_file(tmp_path / f"simplified_rdp{tolerance_rdp}.gpkg")
    assert (
        len(simplified_gdf[simplified_gdf.intersects(point_on_input_and_border)])
        != nb_intersects_with_input
    )

    # With keep_points_on specified, the number of intersections stays the same
    simplified_gdf = input_gdf.copy()
    # assert to evade pyLance warning
    assert isinstance(simplified_gdf, gpd.GeoDataFrame)
    simplified_gdf.geometry = input_gdf.geometry.apply(
        lambda geom: pygeoops.simplify(
            geom,
            algorithm="rdp",
            tolerance=tolerance_rdp,
            keep_points_on=grid_lines_geom,
        )
    )
    simplified_gdf.to_file(
        tmp_path / f"simplified_rdp{tolerance_rdp}_keep_points_on.gpkg"
    )
    assert (
        len(simplified_gdf[simplified_gdf.intersects(point_on_input_and_border)])
        == nb_intersects_with_input
    )


def test_simplify_keep_points_on_vw(tmp_path):
    # Skip test if simplification is not available
    _ = pytest.importorskip("simplification")

    # First init some stuff
    input_path = test_helper.get_testfile("polygon-simplify-onborder-testcase")
    input_gdf = gpd.read_file(input_path)

    # Create geometry where we want the points kept
    grid_gdf = pygeoops.create_grid(
        total_bounds=(
            210431.875 - 1000,
            176640.125 - 1000,
            210431.875 + 1000,
            176640.125 + 1000,
        ),
        nb_columns=2,
        nb_rows=2,
        crs="epsg:31370",
    )
    grid_gdf.to_file(tmp_path / "grid.gpkg")
    grid_coords = [tile.exterior.coords for tile in grid_gdf.geometry]
    grid_lines_geom = shapely.MultiLineString(grid_coords)

    # Test vw (visvalingam-whyatt)
    # Without keep_points_on, the following point that is on the test data +
    # on the grid is removed by vw
    point_on_input_and_border = shapely.Point(210430.125, 176640.125)
    tolerance_vw = 16 * 0.25 * 0.25  # 1m²

    # Determine the number of intersects with the input test data
    nb_intersects_with_input = len(
        input_gdf[input_gdf.intersects(point_on_input_and_border)]
    )
    assert nb_intersects_with_input > 0
    # Test if intersects > 0
    assert len(input_gdf[grid_gdf.intersects(point_on_input_and_border)]) > 0

    # Without keep_points_on the number of intersections changes
    simplified_gdf = input_gdf.copy()
    # assert to evade pyLance warning
    assert isinstance(simplified_gdf, gpd.GeoDataFrame)
    simplified_gdf.geometry = input_gdf.geometry.apply(
        lambda geom: pygeoops.simplify(
            geom,
            algorithm="vw",
            tolerance=tolerance_vw,
        )
    )
    simplified_gdf.to_file(tmp_path / f"simplified_vw{tolerance_vw}.gpkg")
    assert (
        len(simplified_gdf[simplified_gdf.intersects(point_on_input_and_border)])
        != nb_intersects_with_input
    )

    # With keep_points_on specified, the number of intersections stays the same
    simplified_gdf = input_gdf.copy()
    simplified_gdf.geometry = input_gdf.geometry.apply(
        lambda geom: pygeoops.simplify(
            geom,
            algorithm="vw",
            tolerance=tolerance_vw,
            keep_points_on=grid_lines_geom,
        )
    )
    simplified_gdf.to_file(
        tmp_path / f"simplified_vw{tolerance_vw}_keep_points_on.gpkg"
    )
    assert (
        len(simplified_gdf[simplified_gdf.intersects(point_on_input_and_border)])
        == nb_intersects_with_input
    )


def test_simplify_none():
    # Test simplify on None geometry
    result = pygeoops.simplify(None, 1)
    assert result is None


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


def test_simplify_simplification_not_installed():
    # Backup reference to simplification module
    _temp_simplification = None
    if sys.modules.get("simplification"):
        _temp_simplification = sys.modules["simplification"]
    try:
        # Fake that the module is not available
        sys.modules["simplification"] = None

        # Using RDP needs simplification module, so should give ImportError
        pygeoops.simplify(
            geometry=shapely.LineString([(0, 0), (10, 10), (20, 20)]),
            algorithm="rdp",
            tolerance=1,
        )
        assert False
    except ImportError:
        assert True
    finally:
        if _temp_simplification:
            sys.modules["simplification"] = _temp_simplification
        else:
            del sys.modules["simplification"]
