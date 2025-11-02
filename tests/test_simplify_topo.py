import warnings

import geopandas as gpd
import numpy as np
import pytest
import shapely
import test_helper

from pygeoops import _simplify_topo as simplify_topo


@pytest.mark.parametrize(
    "algorithm, tolerance", [("rdp", 1), ("lang", 1), ("lang+", 1), ("vw", 5)]
)
def test_simplify_topo(algorithm, tolerance):
    # Skip test for algorithms that needs simplification lib when it is not available
    if algorithm in ["rdp", "vw"]:
        _ = pytest.importorskip("simplification")

    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input = [poly1, poly2]

    # Test
    result = simplify_topo.simplify_topo(
        input, tolerance=tolerance, algorithm=algorithm
    )

    # Check result
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    # poly 1 can't be simplified and stays the same.
    assert result[0] == input[0]
    # Due to the ~ common boundary between poly1 and poly2, a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up the same as poly1.
    assert result[0] == result[1]


def test_simplify_topo_ducktype_GeoSeries():
    """
    Test returning a GeoSeries when input is a GeoSeries + make sure the indexes from
    the input GeoSeries are retained!
    """
    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input = gpd.GeoSeries([poly1, poly1, poly2])
    input = input.drop(index=1)

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm="lang")

    # Check result
    assert result is not None
    assert type(result) is type(input)
    assert len(result) == len(input)
    # poly 1 can't be simplified and stays the same.
    assert result[0] == input[0]
    # Due to the ~ common boundary between poly1 and poly2, a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up the same as poly1.
    assert result[0] == result[2]


def test_simplify_topo_warning_on_cast():
    """
    Test handling of following warning in simplify_topo:
        topojson/core/dedup.py:107:
        RuntimeWarning: invalid value encountered in cast
        data["bookkeeping_shared_arcs"] = array_bk_sarcs.astype(np.int64).tolist()
    """
    # Prepare test data
    poly1 = shapely.Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    poly2 = shapely.Polygon([(10, 0), (20, 0), (20, 10), (10, 10), (10, 0)])
    poly3 = shapely.Polygon([(20, 0), (30, 0), (30, 10), (20, 10), (20, 0)])
    input = [poly1, poly2, poly3]

    # Test
    with warnings.catch_warnings():
        message = "invalid value encountered in cast.*"
        warnings.filterwarnings(
            action="error", category=RuntimeWarning, message=message
        )
        result = simplify_topo.simplify_topo(input, tolerance=1, algorithm="lang")

    # Check result
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    assert result[0].normalize() == input[0].normalize()
    assert result[1].normalize() == input[1].normalize()


def test_simplify_topo_ducktype_ndarray():
    """
    Test returning a GeoSeries when input is a GeoSeries + make sure the indexes from
    the input GeoSeries are retained!
    """
    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input = np.array([poly1, poly2])

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm="lang")

    # Check result
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    # poly 1 can't be simplified and stays the same.
    assert result[0] == input[0]
    # Due to the ~ common boundary between poly1 and poly2, a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up the same as poly1.
    assert result[0] == result[1]


def test_simplify_topo_GeometryCollection():
    """
    Test with a GeometryCollection as input -> a GeometryCollection will be returned, so
    no extraction of a specific geometry type.
    """
    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    line1 = shapely.Polygon([(10, 10), (0, 10), (0, 0)])
    input = [shapely.GeometryCollection([poly1, line1]), poly2]

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm="lang")

    # Check result
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    for geom_input, geom_result in zip(input, result, strict=True):
        assert type(geom_input) is type(geom_result)


def test_simplify_topo_mixedtypes():
    """
    Test with a list of mixed geometry types as input -> so no extraction of a specific
    geometry type.
    """
    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    line1 = shapely.LineString([(10, 10), (0, 10), (0, 0), (11, 0)])
    input = [poly1, line1]

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm="lang")

    # Check result
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    for geom_input, geom_result in zip(input, result, strict=True):
        assert type(geom_result) is type(geom_input)
        if geom_input.geom_type == "Polygon":
            assert geom_result == geom_input
        else:
            # A point from the polygon is inserted in the line to snap topology
            # boundaries!
            exp_line = shapely.LineString([(10, 10), (0, 10), (0, 0), (10, 0), (11, 0)])
            assert geom_result == exp_line


def test_simplify_topo_None():
    assert simplify_topo.simplify_topo(None, tolerance=1, algorithm="lang") is None
    assert simplify_topo.simplify_topo([None], tolerance=1, algorithm="lang") == [None]


@pytest.mark.parametrize("algorithm", ["lang", "lang+", "rdp", "vw"])
def test_simplify_topo_0dim_ndarray(algorithm):
    # Skip test for algorithms that needs simplification lib when it is not available
    if algorithm in ["rdp", "vw"]:
        _ = pytest.importorskip("simplification")

    line = shapely.Polygon([(10, 10), (0, 10), (0, 0)])
    expected = simplify_topo.simplify_topo(line, tolerance=1, algorithm=algorithm)

    assert (
        simplify_topo.simplify_topo(np.array(line), tolerance=1, algorithm=algorithm)
        == expected
    )


def test_simplify_topo_result_mixed(tmp_path):
    """
    Test with Polygons as input where some of the polygons collapse to lines because of
    the simplification.
    In this case the lines are removed so the output only contains Polygons.
    """
    # Prepare test data
    # a squarish polygon with a narrow triangle excluded to the right
    squarish = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (9, 5), (10, 10)])
    # a narrow triangle that fits in the squarish polygon and will collapse to a line
    narrow_triangle = shapely.Polygon([(10, 10), (9, 5), (10, 0), (10, 10)])
    input = [squarish, narrow_triangle]
    output_path = tmp_path / f"{__name__}_input.png"
    test_helper.plot([squarish, narrow_triangle], output_path)

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm="lang")

    output_path = tmp_path / f"{__name__}_result.png"
    test_helper.plot(result, output_path)

    # Check result
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    for idx, geom_result in enumerate(result):
        if idx == 0:
            assert geom_result == shapely.Polygon(
                [(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)]
            )
        elif idx == 1:
            assert geom_result is None


def test_simplify_topo_result_GeometryCollection(tmp_path):
    """
    Test with Polygons as input where an island in a polygon collapses to a lines
    because of the simplification, resulting in a GeometryCollection.
    In this case the line is removed from the GeometryCollection so the output only
    contains Polygons.
    This tests a specific case because GeometryCollection doesn't have a primitive type.
    """
    # Prepare test data
    # Polygon with a narrow triangle as a hole
    poly_narrow_hole = shapely.Polygon(
        shell=[(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)],
        holes=[[(5, 5), (1, 5), (1, 4), (5, 5)]],
    )
    # Standard polygon
    poly = shapely.Polygon([(30, 10), (20, 10), (20, 0), (30, 0), (30, 10)])
    input = [poly_narrow_hole, poly]
    output_path = tmp_path / f"{__name__}_input.png"
    test_helper.plot([poly_narrow_hole, poly], output_path)

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm="lang")

    output_path = tmp_path / f"{__name__}_result.png"
    test_helper.plot(result, output_path)

    # Check result
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == len(input)
    for idx, geom_result in enumerate(result):
        if idx == 0:
            assert (
                geom_result.normalize()
                == shapely.Polygon(poly_narrow_hole.exterior).normalize()
            )
        elif idx == 1:
            assert geom_result.normalize() == poly.normalize()
