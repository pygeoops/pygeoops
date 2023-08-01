import numpy as np
import pytest
import shapely

from pygeoops import _paramvalidation as paramvalidation


def test_keep_geom_type2dimension():
    # Boolean input
    assert (
        paramvalidation.keep_geom_type2dimension(True, shapely.GeometryCollection())
        == -1
    )
    assert paramvalidation.keep_geom_type2dimension(True, shapely.Point()) == 0
    assert paramvalidation.keep_geom_type2dimension(True, shapely.LineString()) == 1
    assert paramvalidation.keep_geom_type2dimension(True, shapely.Polygon()) == 2
    assert paramvalidation.keep_geom_type2dimension(False, shapely.Polygon()) == -1

    # int/inlike input
    assert paramvalidation.keep_geom_type2dimension(-1, shapely.Polygon()) == -1
    assert paramvalidation.keep_geom_type2dimension(0, shapely.Polygon()) == 0
    assert paramvalidation.keep_geom_type2dimension(1, shapely.Polygon()) == 1
    assert paramvalidation.keep_geom_type2dimension(2, shapely.Polygon()) == 2
    assert paramvalidation.keep_geom_type2dimension(np.int32(2), shapely.Polygon()) == 2

    # Test invalid values
    with pytest.raises(ValueError, match="Invalid value for keep_geom_type"):
        paramvalidation.keep_geom_type2dimension(3, shapely.Polygon())
        paramvalidation.keep_geom_type2dimension(-2, shapely.Polygon())
    with pytest.raises(ValueError, match="Invalid type for keep_geom_type"):
        paramvalidation.keep_geom_type2dimension("bad_type", shapely.Polygon())
