"""Function to create variable width buffers based on M or Z values.

Inspired by the following stackoverflow post:
https://stackoverflow.com/questions/79804624/buffer-a-polyline-by-variable-distance
"""

import logging
from itertools import pairwise

from geopandas import GeoSeries
import numpy as np
from numpy.typing import NDArray
import shapely
from shapely.geometry.base import BaseGeometry
from shapely.geometry import LineString, MultiPoint, Polygon

from pygeoops._general import _extract_0dim_ndarray

logger = logging.getLogger(__name__)


def buffer_by_m(
    line,
    quad_segs: int = 8,
    cap_style: str = "round",
    join_style: str = "round",
    mitre_limit: float = 5.0,
) -> BaseGeometry | NDArray[BaseGeometry] | GeoSeries | None:
    """
    Calculates a variable width buffer for a geometry.

    The buffer distance at each vertex is determined by the M value of that vertex, or
    the Z value if M is not available. If a distance is zero, the resulting buffer will
    taper towards the original point and the result will be a multipolygon where the
    parts touch at that point. If a distance is negative, the resulting buffer will
    omit that point and the result will be a multipolygon with disjoint parts.

    Example output (grey: original polygon, blue: buffer):

    .. plot:: code/buffer_by_m_different_cases.py

    Alternative name: variable width buffer.

    Args:
        line (geometry, GeoSeries or arraylike): a geometry, GeoSeries or arraylike.
        quad_segs (int, optional): The number of segments used to approximate a
            quarter circle. Defaults to 8.
        cap_style (str, optional): The style of the buffer's end caps. One of
            'round', 'flat' or 'square'. Defaults to 'round'.
        join_style (str, optional): The style of the buffer's joins. One of
            'round', 'mitre' or 'bevel'. Defaults to 'round'.
        mitre_limit (float, optional): The mitre limit for 'mitre' join styles.
            Defaults to 5.0.

    Returns:
        geometry, GeoSeries or array_like: the buffer for each of the input
            geometries.

    Example:
    .. code-block:: python

        line = LineString([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]])
        buffer_geom = buffer_by_m(line)

    """
    if line is None:
        return None
    line = _extract_0dim_ndarray(line)

    # If input is not arraylike, treat the single geometry
    if not hasattr(line, "__len__"):
        return _buffer_by_m(
            line=line,
            quad_segs=quad_segs,
            cap_style=cap_style,
            join_style=join_style,
            mitre_limit=mitre_limit,
        )
    else:
        # Arraylike, so treat every geometry in loop
        result = np.array(
            [
                _buffer_by_m(
                    line=geom,
                    quad_segs=quad_segs,
                    cap_style=cap_style,
                    join_style=join_style,
                    mitre_limit=mitre_limit,
                )
                for geom in line
            ]
        )
        if isinstance(line, GeoSeries):
            result = GeoSeries(result, index=line.index, crs=line.crs)

        return result


def _buffer_by_m(
    line: LineString,
    quad_segs,
    cap_style,
    join_style,
    mitre_limit,
) -> BaseGeometry:
    if line.has_m:
        include_m = True
        include_z = False
    elif line.has_z:
        include_m = False
        include_z = True
    else:
        raise ValueError("Input geometry must have M or Z values for buffer distances.")

    # Extract points and distances
    coords = shapely.get_coordinates(line, include_m=include_m, include_z=include_z)
    pts = shapely.points(coords[:, :2])
    distances = coords[:, 2]

    # Buffer each point by its M/Z value
    buffers = shapely.buffer(
        pts,
        distances,
        quad_segs=quad_segs,
        cap_style=cap_style,
        join_style=join_style,
        mitre_limit=mitre_limit,
    )

    # Zero-distance points get empty geometries, so replace those with the original
    # points. Negative distances also result in empty geometries, but we don't want to
    # recuperate those.
    zero_m_indices = np.argwhere(distances == 0)
    buffers[zero_m_indices] = pts[zero_m_indices]

    # Create convex hulls between each pair of buffers
    hull_inputs = [
        MultiPoint(shapely.get_coordinates([buffer1, buffer2]))
        for buffer1, buffer2 in pairwise(buffers)
    ]
    hulls = shapely.convex_hull(hull_inputs)

    # Union all hulls to get the final buffer
    buffer_geom = shapely.union_all(hulls)

    if buffer_geom.is_empty:
        return Polygon()
    return buffer_geom
