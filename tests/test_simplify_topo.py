import geopandas as gpd
import pytest
import shapely

from pygeoops import _simplify_topo as simplify_topo


@pytest.mark.parametrize("algorithm", ["rdp", "lang"])
def test_simplify_topo(algorithm):
    # Skip test if simplification is not available
    _ = pytest.importorskip("simplification")

    # Prepare test data
    poly = shapely.Polygon(
        shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
        holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )
    input_gs = gpd.GeoSeries([poly, poly, poly])
    # Drop some rows to test if series index is retained
    input_gs = input_gs.drop(index=1)

    # Test
    result_gs = simplify_topo.simplify_topo(input_gs, tolerance=1, algorithm=algorithm)

    # Check result
    assert result_gs is not None
    assert isinstance(result_gs, gpd.GeoSeries)
    assert len(result_gs) == len(input_gs)
    assert result_gs.index.to_list() == input_gs.index.to_list()
    assert len(result_gs[0].exterior.coords) < len(input_gs[0].exterior.coords)


def test_simplify_topo_None():
    assert simplify_topo.simplify_topo(None, tolerance=1) is None
    assert simplify_topo.simplify_topo([None], tolerance=1) == [None]
