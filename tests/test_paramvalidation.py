import numpy as np
import pytest
import shapely

from pygeoops import _paramvalidation as valid


@pytest.mark.parametrize(
    "keep_geom_type, geometry, exp_id",
    [
        (True, shapely.GeometryCollection(), 0),
        (True, shapely.Point(), 1),
        (True, shapely.LineString(), 2),
        (True, shapely.Polygon(), 3),
        (False, shapely.Polygon(), 0),
        (0, shapely.Polygon(), 0),
        (1, shapely.Polygon(), 1),
        (2, shapely.Polygon(), 2),
        (3, shapely.Polygon(), 3),
        (np.int32(3), shapely.Polygon(), 3),
        (0, np.array(shapely.Polygon()), 0),
    ],
)
def test_keep_geom_type2primitivetype_id(keep_geom_type, geometry, exp_id):
    assert valid.keep_geom_type2primitivetype_id(keep_geom_type, geometry) == exp_id


def test_keep_geom_type2primitivetype_id_invalid():
    # Test invalid values
    with pytest.raises(ValueError, match="Invalid value for keep_geom_type"):
        valid.keep_geom_type2primitivetype_id(4, shapely.Polygon())
        valid.keep_geom_type2primitivetype_id(-1, shapely.Polygon())
    with pytest.raises(ValueError, match="Invalid type for keep_geom_type"):
        valid.keep_geom_type2primitivetype_id("bad_type", shapely.Polygon())
