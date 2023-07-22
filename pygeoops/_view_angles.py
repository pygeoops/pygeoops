import math
from typing import Tuple

import numpy as np
import shapely
import shapely.geometry


def view_angles(
    viewpoint,
    visible_geom,
):
    """
    Returns the start and end angle where the visible geometry can be seen from the
    viewpoint.

    If one of the parameters is an array, the view angles are calculated for each
    of these with the other parameter. If both parameters are arrays, they should each
    have the same length and the angles will be calculated one on one between the
    corresponding elements.

    Remark: the start angle can be larger than the end angle. E.g. if the visible geom
    is located in the south east of the viewpoint till the north east.

    |view_angles|

    Args:
        viewpoint (Geometry or arraylike): the point that is being viewed from.
        visible_geom (Geometry or arraylike): the visible geometry to calculate the view
            angles to. Only singlepart geometries are supported.

    Returns:
        Tuple or array of floats with for each viewpoint/visible_geom combination the
        start angle and end angle in degrees. Values are between 0 and 360, or np.nan
        for None or empty geometries.

    .. |view_angles| image:: ../_static/images/view_angles.png
        :alt: View angles returned by the function
    """

    # If no param is a list, simple return
    visible_geom_is_arr = hasattr(visible_geom, "__len__")
    viewpoint_is_arr = hasattr(viewpoint, "__len__")
    if not visible_geom_is_arr and not viewpoint_is_arr:
        return _view_angles(viewpoint, visible_geom)

    # At least one of the inputs is arraylike, so prepare input arrays
    if viewpoint_is_arr:
        viewpoint_arr = np.array(viewpoint)
    else:
        viewpoint_arr = np.full(len(visible_geom), viewpoint)
    if visible_geom_is_arr:
        visible_geom_arr = np.array(visible_geom)
    else:
        visible_geom_arr = np.full(len(viewpoint), visible_geom)

    if len(viewpoint_arr) != len(visible_geom_arr):
        raise ValueError(
            "viewpoint and visible_geom are arrays, so they must be the same length"
        )

    # Combine both input arrays
    geoms_arr = np.concatenate(
        [
            np.expand_dims(viewpoint_arr, 1),
            np.expand_dims(visible_geom_arr, 1),
        ],
        axis=1,
    )

    # Function to calculate the view angles for one viewpoint, visible_geom pair
    def calculate_angles(input) -> Tuple[float, float]:
        viewpoint_geom, visible_geom = input
        return _view_angles(viewpoint_geom, visible_geom)

    # Calculate angles for all elements
    angles_arr = np.apply_along_axis(
        calculate_angles,
        arr=geoms_arr,
        axis=1,
    )

    return angles_arr


def _view_angles(
    viewpoint: shapely.Point,
    visible_geom: shapely.Geometry,
) -> Tuple[float, float]:
    """
    Returns the start and end angle where the visible geometry can be seen from the
    viewpoint.

    Remark: the start angle can be larger than the end angle. E.g. if the visible geom
    is located in the south east of the viewpoint till the north east.

    Args:
        viewpoint (Geometry): the point that is being viewed from.
        visible_geom (Geometry): the visible geometry to calculate the
            view angles to. Only single-type geometries are supported.

    Returns:
        Tuple[float, float]: the start angle and end angle for the viewpoint in degrees.
        Values are between 0 and 360, or np.nan if no visible_geom.
    """
    if not isinstance(viewpoint, shapely.Point):
        raise ValueError("viewpoint should be a point")
    if isinstance(visible_geom, shapely.geometry.base.BaseMultipartGeometry):
        raise ValueError("visible_geom can't be a multipart geometry")

    # Prepare the viewpoint
    viewpoint_coords_arr = shapely.get_coordinates(viewpoint)
    if len(viewpoint_coords_arr) != 1:
        raise ValueError(
            f"viewpoint should have one coordinate, not {len(viewpoint_coords_arr)}"
        )
    viewpoint_x = viewpoint_coords_arr[0][0]
    viewpoint_y = viewpoint_coords_arr[0][1]

    # To make it easy to calculate the angles, treat the viewpoint as the origin
    # of the coordinate system.
    def subtract_viewpoint(coords):
        return np.column_stack([coords[:, 0] - viewpoint_x, coords[:, 1] - viewpoint_y])

    visible_geom = shapely.transform(visible_geom, subtract_viewpoint)

    # Get visible coordinates
    visible_coords_arr = shapely.get_coordinates(visible_geom)
    if len(visible_coords_arr) == 0:
        return (np.nan, np.nan)

    # Calculate + convert to 0-360°
    x = visible_coords_arr[:, 0]
    y = visible_coords_arr[:, 1]
    angles_arr = np.rad2deg(np.arctan2(y, x))
    angles_arr = np.where(angles_arr < 0, angles_arr + 360, angles_arr)

    # Check if the visible geometry crosses the 0° line, to make sure angles 0
    # and/or 360 are present if needed
    line_length = 5000000
    if len(angles_arr[angles_arr == 0]) > 0:
        intersects_0 = True
    else:
        line_0 = shapely.linestrings([[[0, 0], [line_length, 0]]])
        intersects_0 = shapely.intersects(visible_geom, line_0).tolist()[0]

    # If visible geom doesn't intersect the 0 angle, it is easy
    if not intersects_0:
        return (angles_arr.min(), angles_arr.max())

    # If visible geom doesn't pass 0 angle to south, it is still easy
    tol = 0.0000000001
    line_SE = shapely.linestrings([[[0, -tol], [line_length, -tol]]])
    if not shapely.intersects(visible_geom, line_SE):
        return (angles_arr.min(), angles_arr.max())
    else:
        # Add 360° angle
        angles_arr = np.append(angles_arr, 360)

    # If visible geom doesn't pass 0 angle to north, still not difficult
    line_NE = shapely.linestrings([[[0, tol], [line_length, tol]]])
    if not shapely.intersects(visible_geom, line_NE):
        # Remove 0 angle if there are still other angles
        angles_nonzero_arr = angles_arr[angles_arr != 0]
        if len(angles_nonzero_arr) > 0:
            # There are other angles than 0, so 0° should NOT be in angles_arr
            return (angles_nonzero_arr.min(), angles_nonzero_arr.max())
    else:
        # 0° should be in angles_arr
        angles_arr = np.append(angles_arr, 0)

    line_180 = shapely.linestrings([[[0, 0], [-line_length, 0]]])
    intersects_180 = shapely.intersects(visible_geom, line_180).tolist()[0]

    # If visible geom doesn't pass 180° angle, return result
    if not intersects_180:
        angle_N_max = angles_arr[angles_arr <= 180].max()
        angle_S_min = angles_arr[angles_arr >= 180].min()
        return (angle_S_min, angle_N_max)
    else:
        # 180° should be in angles_arr
        angles_arr = np.append(angles_arr, 180)

    # It's not clear if/where the geom starts or ends, so "brute-force" search an
    # angle where the geom is not "visible" from the viewpoint.
    # TODO: review code
    angle_prev = None
    for angle in np.sort(angles_arr):
        if angle_prev is None or angle == angle_prev:
            angle_prev = angle
            continue

        # Check if the geom is visible between both angles
        angle_avg = (angle + angle_prev) / 2
        x = line_length * math.cos(angle_avg)
        y = line_length * math.sin(angle_avg)
        line_avg = shapely.linestrings([[[0, 0], [x, y]]])
        intersects_avg = shapely.intersects(visible_geom, line_avg).tolist()[0]
        if not intersects_avg:
            return (angle_prev, angle)

        angle_prev = angle

    # If no angle found where the geom is not visible, it must be all around
    return (0.0, 360.0)
