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
from shapely.geometry import MultiPoint, Polygon

from pygeoops._compat import GEOS_GTE_3_12_0, SHAPELY_GTE_2_1_0
from pygeoops._general import _extract_0dim_ndarray, get_parts_recursive

logger = logging.getLogger(__name__)


def buffer_by_m(
    geometry, quad_segs: int = 8
) -> BaseGeometry | NDArray[BaseGeometry] | GeoSeries | None:
    """
    Calculates a variable width buffer for a geometry.

    The buffer distance at each vertex is determined by the M value of that vertex, or
    the Z value if M is not available.
      - If a distance is zero, the resulting buffer will taper towards the original
        point. If the input is a LineString, this means the result will be a
        MultiPolygon where the parts touch at that point.
      - If a distance is negative or NaN, the resulting buffer will omit that point from
        treatment entirely. If the input is a LineString, this means the result will be
        a MultiPolygon with disjoint parts.

    Support for Polygon input is experimental, feedback welcome.

    Example output (grey: original line, blue: buffer):

    .. plot:: code/buffer_by_m_different_cases.py

    Alternative name: variable width buffer.

    .. versionadded:: 0.6.0

    Args:
        geometry (geometry, GeoSeries or arraylike): a geometry, GeoSeries or arraylike.
        quad_segs (int, optional): The number of segments used to approximate a
            quarter circle. Defaults to 8.

    Returns:
        geometry, GeoSeries or array_like: the buffer for each of the input
            geometries.

    Examples:
        An example of buffering a single LineString with M values:

        .. code-block:: python

            import pygeoops
            import shapely

            line = shapely.LineString([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]])
            buffer_geom = pygeoops.buffer_by_m(line)


        An example where the M values still need to be added to the LineString:

        .. code-block:: python

            import pygeoops
            import shapely

            line = shapely.LineString([[0, 6], [0, 0], [10, 0], [13, 5]])
            distances = [1, 2, 2, 4]
            line_with_m = shapely.LineString(
                [[x, y, m] for (x, y), m in zip(line.coords, distances)]
            )
            buffer_geom = pygeoops.buffer_by_m(line_with_m)


        An example of buffering a GeoDataFrame with LineStrings with M values:

        .. code-block:: python

            import geopandas as gpd
            import pygeoops
            import shapely

            lines_gdf = gpd.GeoDataFrame(
                geometry=[
                    shapely.LineString([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]]),
                    shapely.LineString([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]]),
                ],
            )
            buffer_geoms = lines_gdf.copy()
            buffer_geoms.geometry = pygeoops.buffer_by_m(lines_gdf.geometry)

    """
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)

    # If input is not arraylike, treat the single geometry
    if not hasattr(geometry, "__len__"):
        return _buffer_by_m(geometry=geometry, quad_segs=quad_segs)
    else:
        # Arraylike, so treat every geometry in loop
        result = np.array(
            [_buffer_by_m(geometry=geom, quad_segs=quad_segs) for geom in geometry]
        )
        if isinstance(geometry, GeoSeries):
            result = GeoSeries(result, index=geometry.index, crs=geometry.crs)

        return result


def _buffer_by_m(geometry, quad_segs: int) -> BaseGeometry:
    # Determine which include kwargs to use. Using kwargs as include_m is not available
    # in all Shapely versions.
    include_kwargs = {}
    if SHAPELY_GTE_2_1_0 and GEOS_GTE_3_12_0 and geometry.has_m:
        # has_m is available in Shapely >= 2.1.0 and GEOS >= 3.12.0
        include_kwargs["include_m"] = True
    elif geometry.has_z:
        include_kwargs["include_z"] = True
    else:
        message = "input geometry must have M or Z values for buffer distances."
        if not SHAPELY_GTE_2_1_0 or not GEOS_GTE_3_12_0:
            message += " For M, Shapely >= 2.1.0 and GEOS >= 3.12.0 are needed."
        raise ValueError(f"{message}: got {geometry}")

    # Treat part per part
    partial_buffers = []
    for part in get_parts_recursive(geometry):
        # Extract points and distances
        coords = shapely.get_coordinates(part, **include_kwargs)
        pts = shapely.points(coords[:, :2])
        distances = coords[:, 2]

        # Buffer each point by its M/Z value
        buffers = shapely.buffer(pts, distances, quad_segs=quad_segs)

        if len(buffers) == 1:
            # Single point case: just add the buffer (could be empty polygon)
            partial_buffers.append(buffers)
            continue

        # Zero-distance points get empty geometries, so replace those with the original
        # points. Negative or nan distances also result in empty geometries, but we
        # don't want to recuperate those.
        zero_m_indices = np.argwhere(distances == 0)
        buffers[zero_m_indices] = pts[zero_m_indices]

        # Create convex hulls between each pair of buffers
        hull_inputs = [
            MultiPoint(shapely.get_coordinates([buffer1, buffer2]))
            for buffer1, buffer2 in pairwise(buffers)
        ]
        hulls = shapely.convex_hull(hull_inputs)

        partial_buffers.append(hulls)

        # If the part is a polygon, we want the original areas to be preserved as well.
        if isinstance(part, Polygon):
            partial_buffers.append([part])

    # Union all partial buffers to get the final buffer result.
    buffer_geom = shapely.union_all(np.concatenate(partial_buffers))

    if buffer_geom.is_empty:
        return Polygon()
    return buffer_geom
