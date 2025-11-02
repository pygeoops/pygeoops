import logging
import math

import numpy as np
import shapely
import shapely.coords

logger = logging.getLogger(__name__)


def simplify_coords_lang(
    coords: np.ndarray | list | shapely.coords.CoordinateSequence,
    tolerance: float,
    lookahead: int = 8,
    simplify_lookahead_points: bool = False,
) -> np.ndarray | list:
    """Simplify a line using the lang algorithm.

    The implementation also supports an alternative behaviour of the standard lang
    algorithm to increase the potential number of points removed from the input
    coordinates, without violating the tolerance specified. The standard lang algorithm
    will always retain at least ~ len(coords) / lookahead points in the output, even for
    a line with all collinear point. Par example when lookahead=3, this leads to keeping
    at least 33% of the input points in the output. Using simplify_lookahead_points=True
    will remove this limitation, at the cost of some extra processing time.

    Inspiration for the standard lang implementation came from:
        * https://github.com/giscan/Generalizer/blob/master/simplify.py
        * https://github.com/keszegrobert/polyline-simplification/blob/master/6.%20Lang.ipynb
        * https://web.archive.org/web/20171005193700/http://web.cs.sunyit.edu/~poissad/projects/Curve/about_algorithms/lang.php

    Args:
        coords (Union[np.ndarray, list]): list of coordinates to be simplified.
        tolerance (float): distance tolerance to use.
        lookahead (int, optional): the number of points to consider for removing
            in a moving window. Defaults to 8.
        simplify_lookahead_points (bool, optional): True to also simplify the lookahead
            points. Defaults to False. More info available in the function description.

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
        coords=coords_arr,
        tolerance=tolerance,
        lookahead=lookahead,
        simplify_lookahead_points=simplify_lookahead_points,
    )
    coords_simplified_arr = coords_arr[coords_to_keep_idx]

    # If input was np.ndarray, return np.ndarray, otherwise list
    if isinstance(coords, np.ndarray | shapely.coords.CoordinateSequence):
        return coords_simplified_arr
    else:
        return coords_simplified_arr.tolist()


def simplify_coords_lang_idx(
    coords: np.ndarray | list | shapely.coords.CoordinateSequence,
    tolerance: float,
    lookahead: int = 8,
    simplify_lookahead_points: bool = False,
) -> np.ndarray | list:
    """Simplify a line using the lang algorithm.

    The result is the coordinate indexes to be kept.

    More info about the implemtation + simplify_lookahead_points can be found in the
    description of function simplify_coords_lang.

    Args:
        coords (Union[np.ndarray, list]): list of coordinates to be simplified.
        tolerance (float): distance tolerance to use.
        lookahead (int, optional): the number of points to consider for removing
            in a moving window. Defaults to 8.
        simplify_lookahead_points (bool, optional): True to also simplify the lookahead
            points, resulting in more points being able to be removed in some cases.
            Defaults to False.

    Returns:
        Return the indexes of coordinates that need to be kept after simplification.
        If input coords is an np.ndarray or CoordinateSequence, returns np.ndarray,
        otherwise returns a list.
    """
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

    mask_idx_to_keep = np.ones(nb_points, dtype="bool")
    window_start = 0
    window_end = window_size

    # Apply simplification till the window_start arrives at the last point.
    while True:
        # Check if all points between window_start and window_end are within
        # tolerance distance to the line (window_start, window_end).
        points_outside_tolerance_found = False
        for i in range(window_start + 1, window_end):
            distance = _point_line_distance(
                line_arr[i, 0],
                line_arr[i, 1],
                line_arr[window_start, 0],
                line_arr[window_start, 1],
                line_arr[window_end, 0],
                line_arr[window_end, 1],
            )
            # If distance is nan (= linepoint1 == linepoint2) or > tolerance
            if distance > tolerance:
                points_outside_tolerance_found = True
                break

        # If there were points found outside tolerance distance, we make window smaller
        if points_outside_tolerance_found:
            # Move window_end to previous point, and try again
            window_end -= 1
        else:
            # No point outside tolerance found, so mask points in window and move
            # window_start.
            if not simplify_lookahead_points:
                # In the standard lang implementation the next window always starts with
                # the end point of the previous window.
                mask_idx_to_keep[window_start + 1 : window_end] = False
                window_start = window_end
            # To be able to also mask the "lookahead points", this code path doesn't
            # move the window_start if the current window contained points to be
            # masked. Only the window_end will be moved.
            # This has as effect that the current window_end point will be
            # considered for masking, but increases the effective window_size to
            # check distances for to double when many points are within tolerance,
            # so this will affect performance!
            #
            # Other considered options:
            #   - setting window_start to (window_end -1) would also enable
            #     window_end to be masked in theory, but this doesn't work because
            #     with eg. 90° corners consisting of 2 point within tolerance
            #     "disappear".
            #   - doing two passes, but this effectively at least doubles the
            #     effective tolerance.
            #   - using the mask for not calculating distances for points that are
            #     already masked, but this also increases the effective tolerance

            # Check if there are points in tolerance in the window
            elif not mask_idx_to_keep[window_start + 1 : window_end].any():
                # No points within tolerance found, so move window forward
                window_start = window_end
            else:
                # There are points found, so mask them, but don't move window_start
                mask_idx_to_keep[window_start + 1 : window_end] = False

            if window_start >= nb_points - 1 or window_end >= nb_points - 1:
                break
            window_end += window_size
            if window_end >= nb_points:
                window_end = nb_points - 1

    # Prepare result: convert the mask to a list of indices of points to keep.
    idx_to_keep_arr = mask_idx_to_keep.nonzero()[0]

    # If input was np.ndarray, return np.ndarray, otherwise list
    if isinstance(coords, np.ndarray | shapely.coords.CoordinateSequence):
        return idx_to_keep_arr
    else:
        return idx_to_keep_arr.tolist()


def _point_line_distance(
    point_x: float,
    point_y: float,
    line_x1: float,
    line_y1: float,
    line_x2: float,
    line_y2: float,
) -> float:
    """Calculate the orthogonal distance between the point and line specified.

    Args:
        point_x (float): x coordinate of the point
        point_y (float): y coordinate of the point
        line_x1 (float): x coordinate of the 1st point of the line
        line_y1 (float): y coordinate of the 1st point of the line
        line_x2 (float): x coordinate of the 2nd point of the line
        line_y2 (float): y coordinate of the 2nd point of the line

    Returns:
        float: the orthogonal distance.
    """
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
