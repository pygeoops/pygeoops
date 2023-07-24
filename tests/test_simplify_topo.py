import geopandas as gpd
import pytest
import shapely

from pygeoops import _simplify_topo as simplify_topo


@pytest.mark.parametrize("algorithm", ["rdp", "lang"])
def test_simplify_topo(algorithm):
    # Skip test if simplification is not available
    _ = pytest.importorskip("simplification")

    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input = [poly1, poly2]

    # Test
    result = simplify_topo.simplify_topo(input, tolerance=1, algorithm=algorithm)

    # Check result
    assert result is not None
    assert len(result) == len(input)
    # Due to finding common boundary between poly1 and poly2 a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up th same as poly1.
    assert result[0] == result[1]


@pytest.mark.parametrize("algorithm", ["rdp", "lang"])
def test_simplify_topo_geoseries(algorithm):
    # Skip test if simplification is not available
    _ = pytest.importorskip("simplification")

    # Prepare test data
    poly1 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (10, 0), (10, 10)])
    poly2 = shapely.Polygon([(10, 10), (0, 10), (0, 0), (11, 0), (10, 10)])
    input_gs = gpd.GeoSeries([poly1, poly1, poly2])
    input_gs = input_gs.drop(index=1)

    # Test
    result_gs = simplify_topo.simplify_topo(input_gs, tolerance=1, algorithm=algorithm)

    # Check result
    assert result_gs is not None
    assert isinstance(result_gs, gpd.GeoSeries)
    assert len(result_gs) == len(input_gs)
    # Due to finding common boundary between poly1 and poly2 a point (10, 0) is added
    # to poly2. Simplification removes (11,0), so poly2 ends up th same as poly1.
    assert result_gs[0] == result_gs[2]


def test_simplify_topo_None():
    assert simplify_topo.simplify_topo(None, tolerance=1) is None
    assert simplify_topo.simplify_topo([None], tolerance=1) == [None]
