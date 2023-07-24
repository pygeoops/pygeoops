import geopandas as gpd
import pytest
import shapely

from pygeoops import _simplify_topo as simplify_topo


@pytest.mark.parametrize("algorithm", ["rdp", "lang"])
def test_simplify_topo(algorithm):
    # Skip test if algorithm != "lang" and simplification is not available
    if algorithm != "lang":
        _ = pytest.importorskip("simplification")

    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input = [poly1, poly2]

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm=algorithm)

    # Check result
    assert result is not None
    assert type(result) == type(input)
    assert len(result) == len(input)
    # poly 1 can't be simplified and stays the same.
    assert result[0] == input[0]
    # Due to the ~ common boundary between poly1 and poly2, a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up the same as poly1.
    assert result[0] == result[1]


def test_simplify_topo_array():
    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input_gs = gpd.GeoSeries([poly1, poly1, poly2])
    input_gs = input_gs.drop(index=1)
    input_arr = input_gs.array

    # Test
    result_arr = simplify_topo.simplify_topo(input_arr, tolerance=1, algorithm="lang")

    # Check result
    assert result_arr is not None
    assert type(result_arr) == type(input_arr)
    assert len(result_arr) == len(input_arr)
    # poly 1 can't be simplified and stays the same.
    assert result_arr[0] == input_arr[0]
    # Due to the ~ common boundary between poly1 and poly2, a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up the same as poly1.
    assert result_arr[0] == result_arr[1]


def test_simplify_topo_geoseries():
    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input_gs = gpd.GeoSeries([poly1, poly1, poly2])
    input_gs = input_gs.drop(index=1)

    # Test
    result_gs = simplify_topo.simplify_topo(input_gs, tolerance=1, algorithm="lang")

    # Check result
    assert result_gs is not None
    assert type(result_gs) == type(input_gs)
    assert len(result_gs) == len(input_gs)
    # poly 1 can't be simplified and stays the same.
    assert result_gs[0] == input_gs[0]
    # Due to the ~ common boundary between poly1 and poly2, a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up the same as poly1.
    assert result_gs[0] == result_gs[2]


def test_simplify_topo_list_GeometryCollection():
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
    assert type(result) == type(input)
    assert len(result) == len(input)
    for geom_input, geom_result in zip(input, result):
        assert type(geom_input) == type(geom_result)


def test_simplify_topo_list_mixed():
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
    assert type(result) == type(input)
    assert len(result) == len(input)
    for geom_input, geom_result in zip(input, result):
        assert type(geom_result) == type(geom_input)
        if geom_input.geom_type == "Polygon":
            assert geom_result == geom_input
        else:
            # The point from the polygon in inserted in the line to snap topologies
            exp_line = shapely.LineString([(10, 10), (0, 10), (0, 0), (10, 0), (11, 0)])
            assert geom_result == exp_line


def test_simplify_topo_None():
    assert simplify_topo.simplify_topo(None, tolerance=1, algorithm="lang") is None
    assert simplify_topo.simplify_topo([None], tolerance=1, algorithm="lang") == [None]
