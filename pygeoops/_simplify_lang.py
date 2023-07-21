import logging
import math
from typing import Union

import numpy as np
import shapely
import shapely.coords

logger = logging.getLogger(__name__)


def simplify_coords_lang(
    coords: Union[np.ndarray, list, shapely.coords.CoordinateSequence],
    tolerance: float,
    lookahead: int,
) -> Union[np.ndarray, list]:
    """
    Simplify a line using lang algorithm.

    Args:
        coords (Union[np.ndarray, list]): list of coordinates to be simplified.
        tolerance (float): distance tolerance to use.
        lookahead (int, optional): the number of points to consider for removing
            in a moving window. Defaults to 8.

    Returns:
        Return the coordinates kept after simplification.
        If input coords is np.ndarray or CoordinateSequence, returns np.ndarray,
        otherwise returns a list.
    """

    # Init variables
    if isinstance(coords, np.ndarray):
        coords_arr = coords
    elif isinstance(coords, shapely.coords.CoordinateSequence):
        coords_arr = np.asarray(coords)
    else:
        coords_arr = np.array(list(coords))

    # Determine the coordinates that need to be kept
    coords_to_keep_idx = simplify_coords_lang_idx(
        coords=coords_arr, tolerance=tolerance, lookahead=lookahead
    )
    coords_simplified_arr = coords_arr[coords_to_keep_idx]

    # If input was np.ndarray, return np.ndarray, otherwise list
    if isinstance(coords, (np.ndarray, shapely.coords.CoordinateSequence)):
        return coords_simplified_arr
    else:
        return coords_simplified_arr.tolist()


def simplify_coords_lang_idx(
    coords: Union[np.ndarray, list, shapely.coords.CoordinateSequence],
    tolerance: float,
    lookahead: int = 8,
) -> Union[np.ndarray, list]:
    """
    Simplify a line using lang algorithm and return the coordinate indexes to
    be kept.

    Inspiration for the implementation came from:
        * https://github.com/giscan/Generalizer/blob/master/simplify.py
        * https://github.com/keszegrobert/polyline-simplification/blob/master/6.%20Lang.ipynb
        * https://web.archive.org/web/20171005193700/http://web.cs.sunyit.edu/~poissad/projects/Curve/about_algorithms/lang.php

    Args:
        coords (Union[np.ndarray, list]): list of coordinates to be simplified.
        tolerance (float): distance tolerance to use.
        lookahead (int, optional): the number of points to consider for removing
            in a moving window. Defaults to 8.

    Returns:
        Return the indexes of coordinates that need to be kept after
        simplification.
        If input coords is np.ndarray or CoordinateSequence, returns np.ndarray,
        otherwise returns a list.
    """

    def point_line_distance(
        point_x, point_y, line_x1, line_y1, line_x2, line_y2
    ) -> float:
        denominator = math.sqrt(
            (line_x2 - line_x1) * (line_x2 - line_x1)
            + (line_y2 - line_y1) * (line_y2 - line_y1)
        )
        if denominator == 0:
            return float("Inf")
        else:
            numerator = abs(
                (line_x2 - line_x1) * (line_y1 - point_y)
                - (line_x1 - point_x) * (line_y2 - line_y1)
            )
            return numerator / denominator

    # Init variables
    if isinstance(coords, np.ndarray):
        line_arr = coords
    elif isinstance(coords, shapely.coords.CoordinateSequence):
        line_arr = np.asarray(coords)
    else:
        line_arr = np.array(list(coords))

    # Prepare lookahead
    nb_points = len(line_arr)
    if lookahead == -1:
        window_size = nb_points - 1
    else:
        window_size = min(lookahead, nb_points - 1)

    # mask = np.ones(nb_points), dtype='bool')
    mask = np.zeros(nb_points, dtype="bool")
    mask[0] = True
    window_start = 0
    window_end = window_size

    # Apply simplification till the window_start arrives at the last point.
    ready = False
    while ready is False:
        # Check if all points between window_start and window_end are within
        # tolerance distance to the line (window_start, window_end).
        all_points_in_tolerance = True
        for i in range(window_start + 1, window_end):
            distance = point_line_distance(
                line_arr[i, 0],
                line_arr[i, 1],
                line_arr[window_start, 0],
                line_arr[window_start, 1],
                line_arr[window_end, 0],
                line_arr[window_end, 1],
            )
            # If distance is nan (= linepoint1 == linepoint2) or > tolerance
            if distance > tolerance:
                all_points_in_tolerance = False
                break

        # If not all the points are within the tolerance distance...
        if not all_points_in_tolerance:
            # Move window_end to previous point, and try again
            window_end -= 1
        else:
            # All points are within the tolerance, so they can be masked
            mask[window_end] = True
            # mask[window_start+1:window_end-1] = False

            # Move the window forward
            window_start = window_end
            if window_start == nb_points - 1:
                ready = True
            window_end = window_start + window_size
            if window_end >= nb_points:
                window_end = nb_points - 1

    # Prepare result: convert the mask to a list of indices of points to keep.
    idx_to_keep_arr = mask.nonzero()[0]

    # If input was np.ndarray, return np.ndarray, otherwise list
    if isinstance(coords, (np.ndarray, shapely.coords.CoordinateSequence)):
        return idx_to_keep_arr
    else:
        return idx_to_keep_arr.tolist()
