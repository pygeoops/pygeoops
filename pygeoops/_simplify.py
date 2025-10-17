"""
Module containing utilities to simplify geometries.
"""

import logging

from geopandas import GeoSeries
import numpy as np
from numpy.typing import NDArray
import shapely
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
import shapely.coords
import pygeoops

try:
    import simplification.cutil as simplification

    HAS_SIMPLIFICATION = True
except ImportError:
    HAS_SIMPLIFICATION = False

import pygeoops._general as general
from pygeoops import _simplify_lang as simplify_lang
from pygeoops import _simplify_topo as simplify_topo
from pygeoops._general import _extract_0dim_ndarray

logger = logging.getLogger(__name__)


def simplify(
    geometry,
    tolerance: float,
    algorithm: str = "rdp",
    lookahead: int = 8,
    preserve_topology: bool = True,
    preserve_common_boundaries=False,
    keep_points_on: BaseGeometry | None = None,
) -> BaseGeometry | NDArray[BaseGeometry] | GeoSeries | None:
    """
    Simplify geometry/geometries.

    Example of simplify on a polygon (grey: original, blue: simplified):

    .. plot:: code/simplify_basic.py

    Args:
        geometry (geometry or array_like): a geometry or ndarray of geometries.
        tolerance (float): mandatory tolerance. The type of tolerance depends on the
            ``algorithm`` specified:

                - "rdp", "lang", "lang+": distance to use as tolerance
                - "vw": area to use as tolerance
        algorithm (str, optional): algorithm to use. Defaults to "rdp". Possible
            values:

                - "rdp": Ramer Douglas Peuker algorithm
                - "lang": Lang algorithm
                - "lang+": Lang-based algorithm, but without limit of having at least
                  nb_input_coordinates/lookahead points in the simplified output.
                - "vw": Visvalingal Whyatt algorithm
        lookahead (int, optional): the number of points to consider for removing
            in a moving window. Used for LANG algorithm. Defaults to 8.
        preserve_topology (bool, optional): True to (try to) return valid
            geometries as result. Defaults to True.
        preserve_common_boundaries (bool, optional): True to (try to) maintain common
            boundaries between all geometries in the input geometry list.
            Defaults to False.
        keep_points_on (BaseGeometry], optional): point of the geometry to
            that intersect with these geometries are not removed. Defaults to None.

    Raises:
        Exception: [description]

    Returns:
        Union[BaseGeometry, NDArray[BaseGeometry], GeoSeries, None]: the
            simplified version of the input geometry/geometries.

    Examples:
        The simplify function has some advanced options to control the simplification
        behaviour.

        Using the `keep_points_on` parameter, you can specify geometries/locations
        where points should be preserved during simplification. In the following plot
        you see the result if you exclude the points on the minimum bounding box of the
        polygon being removed.

        .. plot:: code/simplify_keep_points_on.py
    """
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)
    algorithm = algorithm.lower()

    # If common boundaries need to be preserved, use topologic implementation
    if preserve_common_boundaries:
        if not preserve_topology:
            raise ValueError(
                "The combination of preserve_common_boundaries=True and "
                "preserve_topology=False is not supported."
            )
        return simplify_topo.simplify_topo(
            geometry=geometry,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            keep_points_on=keep_points_on,
        )

    # If the algorithm is rdp and no keep_points_on, use the faster shapely
    if algorithm == "rdp" and keep_points_on is None:
        return shapely.simplify(
            geometry, tolerance=tolerance, preserve_topology=preserve_topology
        )

    # If input is arraylike, apply to all elements
    if hasattr(geometry, "__len__"):
        result = np.array(
            [
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
        )
        if isinstance(geometry, GeoSeries):
            result = GeoSeries(result, index=geometry.index, crs=geometry.crs)
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
    geometry: BaseGeometry | None,
    tolerance: float,
    algorithm: str = "rdp",
    lookahead: int = 8,
    preserve_topology: bool = True,
    keep_points_on: BaseGeometry | None = None,
) -> BaseGeometry | None:
    # Init:
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)
    algorithm = algorithm.lower()

    # If the algorithm is rdp and no keep_points_on, use shapely
    if algorithm == "rdp" and keep_points_on is None:
        return shapely.simplify(
            geometry, tolerance=tolerance, preserve_topology=preserve_topology
        )

    # Check algorythm
    simplify_lookahead_points = False
    if algorithm in ["rdp", "vw"]:
        if not HAS_SIMPLIFICATION:
            raise ImportError(
                "To use simplify_ext using rdp or vw, first install simplification "
                "with 'pip install simplification'"
            )
    elif algorithm == "lang":
        pass
    elif "lang+":
        simplify_lookahead_points = True
    else:
        raise ValueError(f"Unsupported algorithm specified: {algorithm}")

    # Loop over the rings, and simplify them one by one...
    # If the geometry is None, just return...
    if isinstance(geometry, shapely.Point | shapely.MultiPoint):
        # Point or MultiPoint cannot be simplified
        return geometry
    elif isinstance(geometry, shapely.LineString):
        result_geom = simplify_linestring(
            linestring=geometry,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            simplify_lookahead_points=simplify_lookahead_points,
            preserve_topology=preserve_topology,
            keep_points_on=keep_points_on,
        )
    elif isinstance(geometry, shapely.Polygon):
        result_geom = simplify_polygon(
            polygon=geometry,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            simplify_lookahead_points=simplify_lookahead_points,
            preserve_topology=preserve_topology,
            keep_points_on=keep_points_on,
        )
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


# Apply the simplification (can result in multipolygons)
def simplify_polygon(
    polygon: shapely.Polygon,
    tolerance: float,
    algorithm: str,
    lookahead: int,
    simplify_lookahead_points: bool,
    preserve_topology: bool,
    keep_points_on: BaseGeometry | None,
) -> shapely.Polygon | shapely.MultiPolygon | None:
    # First simplify exterior ring
    assert polygon.exterior is not None
    exterior_simpl = simplify_coords(
        polygon.exterior.coords,
        tolerance=tolerance,
        algorithm=algorithm,
        lookahead=lookahead,
        simplify_lookahead_points=simplify_lookahead_points,
        keep_points_on=keep_points_on,
    )

    # If simplify result is None or not enough points
    if exterior_simpl is None or len(exterior_simpl) < 3:
        if preserve_topology:
            # If topology needs to be preserved, keep original ring
            exterior_simpl = polygon.exterior.coords
        else:
            # No use to continue... result is None polygon
            return None

    # Now simplify interior rings
    interiors_simpl = []
    for interior in polygon.interiors:
        interior_simpl = simplify_coords(
            coords=interior.coords,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            simplify_lookahead_points=simplify_lookahead_points,
            keep_points_on=keep_points_on,
        )

        # If simplified version is ring, add it
        if interior_simpl is not None and len(interior_simpl) >= 3:
            interiors_simpl.append(interior_simpl)
        elif preserve_topology:
            # If result is no ring, but topology needs to be preserved,
            # add original ring
            interiors_simpl.append(interior.coords)

    result_poly = shapely.Polygon(exterior_simpl, interiors_simpl)

    # Extract only polygons as result + try to make valid
    result_poly = general.collection_extract(
        shapely.make_valid(result_poly), primitivetype=pygeoops.PrimitiveType.POLYGON
    )

    # If the result is None and the topology needs to be preserved, return
    # original polygon
    if preserve_topology and result_poly is None:
        return polygon

    return result_poly


def simplify_linestring(
    linestring: shapely.LineString,
    tolerance: float,
    algorithm: str,
    lookahead: int,
    simplify_lookahead_points: bool,
    preserve_topology: bool,
    keep_points_on: BaseGeometry | None,
) -> shapely.LineString:
    # If the linestring cannot be simplified, return it
    if linestring is None or len(linestring.coords) <= 2:
        return linestring

    # Simplify
    coords_simpl = simplify_coords(
        coords=linestring.coords,
        tolerance=tolerance,
        algorithm=algorithm,
        lookahead=lookahead,
        simplify_lookahead_points=simplify_lookahead_points,
        keep_points_on=keep_points_on,
    )

    # If the result is no line anymore
    if coords_simpl is None or len(coords_simpl) < 2:
        if preserve_topology:
            # If preserve_topology is True, return original line
            return linestring
        else:
            return None

    return shapely.LineString(coords_simpl)


def simplify_coords(
    coords: np.ndarray | shapely.coords.CoordinateSequence,
    tolerance: float,
    algorithm: str,
    lookahead: int,
    simplify_lookahead_points: bool,
    keep_points_on: BaseGeometry | None,
) -> np.ndarray:
    if isinstance(coords, shapely.coords.CoordinateSequence):
        coords = np.asarray(coords)
    # Determine the indexes of the coordinates to keep after simplification
    if algorithm == "rdp":
        coords_simplify_idx = simplification.simplify_coords_idx(coords, tolerance)
    elif algorithm == "vw":
        # The simplification library also has a topology preserving variant of vw, but
        # it doesn't support returning indexes, so is not used.
        coords_simplify_idx = simplification.simplify_coords_vw_idx(coords, tolerance)
    elif algorithm in ["lang", "lang+"]:
        coords_simplify_idx = simplify_lang.simplify_coords_lang_idx(
            coords=coords,
            tolerance=tolerance,
            lookahead=lookahead,
            simplify_lookahead_points=simplify_lookahead_points,
        )
    else:
        raise ValueError(f"Unsupported algorithm specified: {algorithm}")

    coords_to_drop_onborder_idx = []
    if keep_points_on is not None:
        # Check if there are coordinates that would be removed that should be kept
        shapely.prepare(keep_points_on)
        coords_to_drop_mask = np.ones(len(coords), dtype="bool")
        coords_to_drop_mask[coords_simplify_idx] = False
        coords_to_drop_idx = coords_to_drop_mask.nonzero()[0]

        coords_to_drop_points = shapely.points(coords[coords_to_drop_idx])
        coords_to_drop_onborder = keep_points_on.intersects(coords_to_drop_points)
        coords_to_drop_onborder_idx = coords_to_drop_idx[coords_to_drop_onborder]

    # Extracts coordinates that need to be kept
    coords_to_keep_idx = coords_simplify_idx
    if len(coords_to_drop_onborder_idx) > 0:
        coords_to_keep_idx = np.concatenate(
            [coords_to_keep_idx, coords_to_drop_onborder_idx], dtype=np.int64
        )
        # Indexes of coordinates to keep need to be sorted
        coords_to_keep_idx = np.sort(coords_to_keep_idx)

    return coords[coords_to_keep_idx]
