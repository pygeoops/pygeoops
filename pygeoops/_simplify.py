import logging
import math
from typing import Optional, Union

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
import shapely.coords

import pygeoops._general as general
from pygeoops._general import PrimitiveType

logger = logging.getLogger(__name__)


def simplify(
    geometry: Optional[BaseGeometry],
    tolerance: float,
    algorithm: str = "rdp",
    lookahead: int = 8,
    preserve_topology: bool = True,
    keep_points_on: Optional[BaseGeometry] = None,
) -> Optional[BaseGeometry]:
    """
    Simplify the geometry.

    Args:
        geometry (shapely geometry): the geometry to simplify
        tolerance (float): mandatory for the following algorithms:
            * "rdp": distance to use as tolerance
            * "lang": distance to use as tolerance
            * "vw": area to use as tolerance
        algorithm (str, optional): algorithm to use. Defaults to "rdp".
            * "rdp": Ramer Douglas Peuker
            * "lang": Lang
            * "vw": Visvalingal Whyatt
        lookahead (int, optional): the number of points to consider for removing
            in a moving window. Used for LANG algorithm. Defaults to 8.
        preserve_topology (bool, optional): True to (try to) return valid
            geometries as result. Defaults to True.
        keep_points_on (BaseGeometry], optional): point of the geometry to
            that intersect with these geometries are not removed. Defaults to None.

    Raises:
        Exception: [description]
        Exception: [description]
        Exception: [description]

    Returns:
        BaseGeometry: The simplified version of the geometry.
    """
    # Init:
    if geometry is None:
        return None
    if algorithm in [
        "rdp",
        "vw",
    ]:
        try:
            import simplification.cutil as simplification
        except ImportError as ex:
            raise ImportError(
                "To use simplify_ext using rdp or vw, first install "
                "simplification with 'pip install simplification'"
            ) from ex
    elif algorithm == "lang":
        pass
    else:
        raise ValueError(f"Unsupported algorythm specified: {algorithm}")

    # Define some inline funtions
    # Apply the simplification (can result in multipolygons)
    def simplify_polygon(
        polygon: shapely.Polygon,
    ) -> Union[shapely.Polygon, shapely.MultiPolygon, None]:
        # First simplify exterior ring
        assert polygon.exterior is not None
        exterior_simplified = simplify_coords(polygon.exterior.coords)

        # If topology needs to be preserved, keep original ring if simplify results in
        # None or not enough points
        if preserve_topology is True and (
            exterior_simplified is None or len(exterior_simplified) < 3
        ):
            exterior_simplified = polygon.exterior.coords

        # Now simplify interior rings
        interiors_simplified = []
        for interior in polygon.interiors:
            interior_simplified = simplify_coords(interior.coords)

            # If simplified version is ring, add it
            if interior_simplified is not None and len(interior_simplified) >= 3:
                interiors_simplified.append(interior_simplified)
            elif preserve_topology is True:
                # If result is no ring, but topology needs to be preserved,
                # add original ring
                interiors_simplified.append(interior.coords)

        result_poly = shapely.Polygon(exterior_simplified, interiors_simplified)

        # Extract only polygons as result + try to make valid
        result_poly = general.collection_extract(
            shapely.make_valid(result_poly), primitivetype=PrimitiveType.POLYGON
        )

        # If the result is None and the topology needs to be preserved, return
        # original polygon
        if preserve_topology is True and result_poly is None:
            return polygon

        return result_poly

    def simplify_linestring(linestring: shapely.LineString) -> shapely.LineString:
        # If the linestring cannot be simplified, return it
        if linestring is None or len(linestring.coords) <= 2:
            return linestring

        # Simplify
        coords_simplified = simplify_coords(linestring.coords)

        # If preserve_topology is True and the result is no line anymore, return
        # original line
        if preserve_topology is True and (
            coords_simplified is None or len(coords_simplified) < 2
        ):
            return linestring
        else:
            return shapely.LineString(coords_simplified)

    def simplify_coords(
        coords: Union[np.ndarray, shapely.coords.CoordinateSequence]
    ) -> np.ndarray:
        if isinstance(coords, shapely.coords.CoordinateSequence):
            coords = np.asarray(coords)
        # Determine the indexes of the coordinates to keep after simplification
        if algorithm == "rdp":
            coords_simplify_idx = simplification.simplify_coords_idx(coords, tolerance)
        elif algorithm == "vw":
            coords_simplify_idx = simplification.simplify_coords_vw_idx(
                coords, tolerance
            )
        elif algorithm == "lang":
            coords_simplify_idx = _simplify_coords_lang_idx(
                coords, tolerance, lookahead=lookahead
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        coords_on_border_idx = []
        if keep_points_on is not None:
            coords_gdf = gpd.GeoDataFrame(
                geometry=list(shapely.MultiPoint(coords).geoms)
            )
            coords_on_border_series = coords_gdf.intersects(keep_points_on)
            coords_on_border_idx = np.array(
                coords_on_border_series.index[coords_on_border_series]
            )

        # Extracts coordinates that need to be kept
        coords_to_keep = coords_simplify_idx
        if len(coords_on_border_idx) > 0:
            coords_to_keep = np.concatenate(
                [coords_to_keep, coords_on_border_idx], dtype=np.int64
            )
        return coords[coords_to_keep]

    # Loop over the rings, and simplify them one by one...
    # If the geometry is None, just return...
    if geometry is None:
        raise Exception("geom input parameter should not be None")
    elif isinstance(geometry, shapely.Point):
        # Point cannot be simplified
        return geometry
    elif isinstance(geometry, shapely.MultiPoint):
        # MultiPoint cannot be simplified
        return geometry
    elif isinstance(geometry, shapely.LineString):
        result_geom = simplify_linestring(geometry)
    elif isinstance(geometry, shapely.Polygon):
        result_geom = simplify_polygon(geometry)
    elif isinstance(geometry, BaseMultipartGeometry):
        # If it is a multi-part, recursively call simplify for all parts.
        simplified_geometries = []
        for geom in geometry.geoms:
            simplified_geometries.append(
                simplify(
                    geom,
                    tolerance=tolerance,
                    algorithm=algorithm,
                    lookahead=lookahead,
                    preserve_topology=preserve_topology,
                    keep_points_on=keep_points_on,
                )
            )
        result_geom = general.collect(simplified_geometries)
    else:
        raise ValueError(f"Unsupported geom_type: {geometry.geom_type}, {geometry}")

    return shapely.make_valid(result_geom)


def _simplify_coords_lang(
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
        If input coords is np.ndarray, returns np.ndarray, otherwise returns a list.
    """

    # Init variables
    if isinstance(coords, np.ndarray):
        coords_arr = coords
    elif isinstance(coords, shapely.coords.CoordinateSequence):
        coords_arr = np.asarray(coords)
    else:
        coords_arr = np.array(list(coords))

    # Determine the coordinates that need to be kept
    coords_to_keep_idx = _simplify_coords_lang_idx(
        coords=coords_arr, tolerance=tolerance, lookahead=lookahead
    )
    coords_simplified_arr = coords_arr[coords_to_keep_idx]

    # If input was np.ndarray, return np.ndarray, otherwise list
    if isinstance(coords, (np.ndarray, shapely.coords.CoordinateSequence)):
        return coords_simplified_arr
    else:
        return coords_simplified_arr.tolist()


def _simplify_coords_lang_idx(
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
        If input coords is np.ndarray, returns np.ndarray, otherwise returns a list.
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
    if isinstance(coords, np.ndarray):
        return idx_to_keep_arr
    else:
        return idx_to_keep_arr.tolist()
