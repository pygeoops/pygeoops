from typing import List, Tuple

import numpy as np
import pytest
import shapely
import shapely.affinity
from shapely import from_wkt

import pygeoops


def get_testdata() -> (
    Tuple[shapely.Point, List[shapely.Geometry], List[Tuple[str, str]]]
):
    # Viewpoint
    viewpoint = shapely.Point(10, 20)

    # Prepare visible_geom data
    data = [
        ["Geom EMPTY", np.nan, np.nan, shapely.Polygon()],
        ["Geom None", np.nan, np.nan, None],
        ["NE_SE", 315.0, 45.0, from_wkt("POLYGON((1 1, 1 -1, 2 -1, 2 1, 1 1))")],
        ["NE, y=0", 0.0, 45.0, from_wkt("POLYGON((1 0, 1 1, 2 1, 2 0, 1 0))")],
        ["NW", 135.0, 180.0, from_wkt("POLYGON((-1 0, -1 1, -2 1, -2 0, -1 0))")],
        ["NW_SE", 135.0, 315.0, from_wkt("POLYGON((-1 1, -1 0.5, 1 -1, -3 1, -1 1))")],
    ]
    visible_geoms = [
        shapely.affinity.translate(row[3], xoff=viewpoint.x, yoff=viewpoint.y)
        if row[3] is not None
        else None
        for row in data
    ]
    expected_angles = [(row[1], row[2]) for row in data]

    return (viewpoint, visible_geoms, expected_angles)


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

    with pytest.raises(ValueError, match="viewpoint should have one coordinate, not 0"):
        pygeoops.view_angles(shapely.Point(), shapely.Polygon())

    with pytest.raises(
        ValueError,
        match="viewpoint and visible_geom are arrays, so they must be the same length",
    ):
        pygeoops.view_angles([shapely.Point(), shapely.Point()], [shapely.Polygon()])


def test_view_angles_arraylike():
    """
    Test view_angles with arraylike input(s).
    """
    viewpoint, visible_geoms, expected_angles = get_testdata()

    # Run test with viewpoint a Point and visible_geoms an array
    # ----------------------------------------------------------
    angles_arr = pygeoops.view_angles(viewpoint, visible_geoms)

    # Compare expected results
    assert np.array_equal(angles_arr, np.array(expected_angles), equal_nan=True)

    # Run test with viewpoint + visible_goms as an array
    # --------------------------------------------------
    viewpoint_arr = np.array([viewpoint for i in range(len(visible_geoms))])
    angles_arr = pygeoops.view_angles(viewpoint_arr, visible_geoms)

    # Compare expected results
    assert np.array_equal(angles_arr, np.array(expected_angles), equal_nan=True)

    # Run test with viewpoint an array and visible_geoms a single geometry
    # --------------------------------------------------------------------
    viewpoint_arr = np.array([viewpoint for i in range(len(visible_geoms))])
    visible_geom = visible_geoms[3]
    angles_arr = pygeoops.view_angles(viewpoint_arr, visible_geom)

    # Compare expected results
    exp_angles_arr = np.full((len(viewpoint_arr), 2), expected_angles[3])
    assert np.array_equal(angles_arr, exp_angles_arr, equal_nan=True)
