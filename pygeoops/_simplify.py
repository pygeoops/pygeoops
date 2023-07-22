# -*- coding: utf-8 -*-
"""
Module containing utilities to simplify geometries.
"""

import logging
from typing import Optional, Union

import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
import shapely.coords

try:
    import simplification.cutil as simplification

    HAS_SIMPLIFICATION = True
except ImportError:
    HAS_SIMPLIFICATION = False

import pygeoops._general as general
from pygeoops._general import PrimitiveType
from pygeoops import _simplify_lang as simplify_lang

logger = logging.getLogger(__name__)


def simplify(
    geometry: Union[BaseGeometry, np.ndarray, list, None],
    tolerance: float,
    algorithm: str = "rdp",
    lookahead: int = 8,
    preserve_topology: bool = True,
    keep_points_on: Optional[BaseGeometry] = None,
) -> Union[BaseGeometry, np.ndarray, list, None]:
    """
    Simplify the geometry.

    Args:
        geometry (geometry or array_like): a geometry or ndarray of geometries
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
    if geometry is None:
        return None

    # Check if input is arraylike
    if hasattr(geometry, "__len__"):
        # Treat every geometry
        result = [
            _simplify(
                geometry=geom,
                tolerance=tolerance,
                algorithm=algorithm,
                lookahead=lookahead,
                preserve_topology=preserve_topology,
                keep_points_on=keep_points_on,
            )
            for geom in geometry
        ]
        return result
    else:
        return _simplify(
            geometry=geometry,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            preserve_topology=preserve_topology,
            keep_points_on=keep_points_on,
        )


def _simplify(
    geometry: Optional[BaseGeometry],
    tolerance: float,
    algorithm: str = "rdp",
    lookahead: int = 8,
    preserve_topology: bool = True,
    keep_points_on: Optional[BaseGeometry] = None,
) -> Optional[BaseGeometry]:
    # Init:
    if geometry is None:
        return None
    if algorithm in ["rdp", "vw"]:
        if not HAS_SIMPLIFICATION:
            raise ImportError(
                "To use simplify_ext using rdp or vw, first install simplification "
                "with 'pip install simplification'"
            )
    elif algorithm == "lang":
        pass
    else:
        raise ValueError(f"Unsupported algorythm specified: {algorithm}")

    # Define some inline funtions
    # Apply the simplification (can result in multipolygons)
    def simplify_polygon(
        polygon: shapely.Polygon, keep_points_on: Optional[BaseGeometry]
    ) -> Union[shapely.Polygon, shapely.MultiPolygon, None]:
        # First simplify exterior ring
        assert polygon.exterior is not None
        exterior_simplified = simplify_coords(polygon.exterior.coords, keep_points_on)

        # If topology needs to be preserved, keep original ring if simplify results in
        # None or not enough points
        if preserve_topology is True and (
            exterior_simplified is None or len(exterior_simplified) < 3
        ):
            exterior_simplified = polygon.exterior.coords

        # Now simplify interior rings
        interiors_simplified = []
        for interior in polygon.interiors:
            interior_simplified = simplify_coords(interior.coords, keep_points_on)

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

    def simplify_linestring(
        linestring: shapely.LineString, keep_points_on: Optional[BaseGeometry]
    ) -> shapely.LineString:
        # If the linestring cannot be simplified, return it
        if linestring is None or len(linestring.coords) <= 2:
            return linestring

        # Simplify
        coords_simplified = simplify_coords(linestring.coords, keep_points_on)

        # If preserve_topology is True and the result is no line anymore, return
        # original line
        if preserve_topology is True and (
            coords_simplified is None or len(coords_simplified) < 2
        ):
            return linestring
        else:
            return shapely.LineString(coords_simplified)

    def simplify_coords(
        coords: Union[np.ndarray, shapely.coords.CoordinateSequence],
        keep_points_on: Optional[BaseGeometry],
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
            coords_simplify_idx = simplify_lang.simplify_coords_lang_idx(
                coords, tolerance, lookahead=lookahead
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        coords_on_border_idx = []
        if keep_points_on is not None:
            # Check if there are coordinates that would be removed that should be kept
            shapely.prepare(keep_points_on)
            coords_to_drop_mask = np.ones(len(coords), dtype=int)
            coords_to_drop_mask[coords_simplify_idx] = 0
            coords_to_drop_idx = coords_to_drop_mask.nonzero()[0]

            coords_points = shapely.points(coords[coords_to_drop_idx])
            coords_to_drop_on_border = keep_points_on.intersects(coords_points)
            coords_on_border_idx = coords_to_drop_idx[coords_to_drop_on_border]

        # Extracts coordinates that need to be kept
        coords_to_keep = coords_simplify_idx
        if len(coords_on_border_idx) > 0:
            coords_to_keep = np.concatenate(
                [coords_to_keep, coords_on_border_idx], dtype=np.int64
            )
            coords_to_keep = np.sort(coords_to_keep)

        return coords[coords_to_keep]

    # Loop over the rings, and simplify them one by one...
    # If the geometry is None, just return...
    if geometry is None:
        raise ValueError("geom input parameter should not be None")
    elif isinstance(geometry, shapely.Point):
        # Point cannot be simplified
        return geometry
    elif isinstance(geometry, shapely.MultiPoint):
        # MultiPoint cannot be simplified
        return geometry
    elif isinstance(geometry, shapely.LineString):
        result_geom = simplify_linestring(geometry, keep_points_on)
    elif isinstance(geometry, shapely.Polygon):
        result_geom = simplify_polygon(geometry, keep_points_on)
    elif isinstance(geometry, BaseMultipartGeometry):
        # If it is a multi-part, recursively call simplify for all parts.
        simplified_geometries = [
            _simplify(
                geom,
                tolerance=tolerance,
                algorithm=algorithm,
                lookahead=lookahead,
                preserve_topology=preserve_topology,
                keep_points_on=keep_points_on,
            )
            for geom in geometry.geoms
        ]
        result_geom = general.collect(simplified_geometries)
    else:
        raise ValueError(f"Unsupported geometrytype: {geometry}")

    return shapely.make_valid(result_geom)
