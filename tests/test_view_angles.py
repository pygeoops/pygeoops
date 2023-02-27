
import numpy as np
import pytest
import shapely

import pygeoops


@pytest.mark.parametrize(
    "descr, exp_angle_start, exp_angle_end, wkt",
    [
        ["Geom EMPTY", np.nan, np.nan, "POLYGON(EMPTY)"],
        ["Geom None", np.nan, np.nan, None],
        [
            "NE>NW_<360",
            45.0,
            135.0,
            "POLYGON((1 1, 1 -1, -1 -1, -1 1, -2 -2, 2 -2, 1 1))",
        ],
        [
            "NE>SW_<360",
            0.0,
            270.0,
            "POLYGON((1 0, 0 1, -1 0, 0 -1, -1 -1, -2 2, 2 2, 1 0))",
        ],
        [
            "NE>SW_360",
            0.0,
            360.0,
            "POLYGON((1 0, 1 1, -1 1, -1 -1, 1 -1, 2 0, 2 -2, -2 -2, -2 2, 2 2, 1 0))",
        ],
        ["NE_SE", 315.0, 45.0, "POLYGON((1 1, 1 -1, 2 -1, 2 1, 1 1))"],
        ["NE, y=0", 0.0, 45.0, "POLYGON((1 0, 1 1, 2 1, 2 0, 1 0))"],
        ["NW", 135.0, 180.0, "POLYGON((-1 0, -1 1, -2 1, -2 0, -1 0))"],
        ["NW_SE", 135.0, 315.0, "POLYGON((-1 1, -1 0.5, 1 -1, -3 1, -1 1))"],
        ["NW_SW", 135.0, 225.0, "POLYGON((-1 -1, -1 1, -2 1, -2 -1, -1 -1))"],
        [
            "NW>SE",
            135.0,
            360.0,
            "POLYGON((-1 1, -1 -1, 1 -1, 1 0, 2 -2, -2 -2, -1 1))",
        ],
        ["SE, y!=0", 270.0, 315.0, "POLYGON((1 -1, 0 -1, 0 -2, 1 -1))"],
        ["SE, y=0", 315.0, 360.0, "POLYGON((1 0, 1 -1, 2 -1, 2 0, 1 0))"],
        [
            "SW>NW",
            225.0,
            135.0,
            "POLYGON((-1 -1, 2 -1, -1 1, 3 1, 3 -2, -1 -1))",
        ],
    ],
)
def test_view_angles(descr, exp_angle_start, exp_angle_end, wkt):
    # View location
    viewpoint_x = 10
    viewpoint_y = 20
    viewpoint = shapely.from_wkt(f"POINT({viewpoint_x} {viewpoint_y})")
    visible_geom_orig = shapely.from_wkt(wkt)

    # The raw visible geoms are based on a view location of 0,0. Adapt it to the
    # view location used as 0,0 wouldn't have a good test coverage.
    def add_viewpoint(coords):
        return np.column_stack([coords[:, 0] + viewpoint_x, coords[:, 1] + viewpoint_y])

    visible_geom = shapely.transform(visible_geom_orig, add_viewpoint)

    # Go!
    view_angles = pygeoops.view_angles(viewpoint, visible_geom)
    assert view_angles == (exp_angle_start, exp_angle_end)


def test_view_angles_invalid_input():
    with pytest.raises(ValueError, match="viewpoint should be a point"):
        pygeoops.view_angles(shapely.Polygon(), shapely.Polygon())

    with pytest.raises(ValueError, match="visible_geom can't be a multipart geometry"):
        pygeoops.view_angles(shapely.Point(), shapely.MultiPolygon())
