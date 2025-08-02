import logging
import math

from geopandas import GeoSeries
import numpy as np
from numpy.typing import NDArray
import shapely
from shapely.geometry.base import BaseGeometry

from pygeoops._general import _extract_0dim_ndarray, format_short
from pygeoops import _extend_line


logger = logging.getLogger(__name__)


def centerline(
    geometry,
    densify_distance: float = -1,
    min_branch_length: float = -1,
    simplifytolerance: float = -0.25,
    extend: bool = False,
) -> BaseGeometry | NDArray[BaseGeometry] | GeoSeries | None:
    """
    Calculates an approximated centerline for a polygon.

    Negative values for the algorithm parameters will result in an automatic
    optimisation based on the average geometry width for each input geometry.

    Alternative name: medial axis.

    Example output:

    |centerline_L_shape|

    Args:
        geometry (geometry, GeoSeries or arraylike): a geometry, GeoSeries or arraylike.
        densify_distance (float, optional): densify input geometry
            so each segment has maximum this length. A reasonable value is the typical
            minimal width of the input geometries. If a larger value is used centerlines
            might have holes on narrow places in the input geometry. The smaller the
            value choosen, the longer the processing will take. Defaults to -1.

              - value = 0: no densification
              - value > 0: densify using this value
              - value < 0: densify_distance = average width of geometry * abs(value)
        min_branch_length (float, optional): minimum length for branches of the main
            centerline. Defaults to -1.

              - value = 0: no branch filtering
              - value > 0: filter branches shorter than this value
              - value < 0: min_branch_length = average width of geometry * abs(value)
        simplifytolerance (float, optional): tolerance to simplify the resulting
            centerline (using Douglas-Peucker algoritm). Defaults to -0.25.

              - value = 0: no simplify
              - value > 0: simplify with this value as tolerance
              - value < 0: simplifytolerance = average width of geometry * abs(value)
        extend (bool, optional): extend the centerline to the edge of the geometry.

    Returns:
        geometry, GeoSeries or array_like: the centerline for each of the input
            geometries.

    .. |centerline_L_shape| image:: ../_static/images/centerline_fancy_Lshape.png
        :alt: Centerline of a fancy L shaped polygon
    """
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)

    # If input is arraylike, treat every geometry in loop
    if hasattr(geometry, "__len__"):
        result = np.array(
            [
                _centerline(
                    geom=geom,
                    densify_distance=densify_distance,
                    min_branch_length=min_branch_length,
                    simplifytolerance=simplifytolerance,
                    extend=extend,
                )
                for geom in geometry
            ]
        )
        if isinstance(geometry, GeoSeries):
            result = GeoSeries(result, index=geometry.index, crs=geometry.crs)
        return result
    else:
        return _centerline(
            geom=geometry,
            densify_distance=densify_distance,
            min_branch_length=min_branch_length,
            simplifytolerance=simplifytolerance,
            extend=extend,
        )


def _centerline(
    geom: BaseGeometry | None,
    densify_distance: float = -1,
    min_branch_length: float = -1,
    simplifytolerance: float = -0.25,
    extend: bool = False,
) -> BaseGeometry | None:
    if geom is None or geom.is_empty:
        return None

    try:
        # Densify lines in the input
        average_width = None
        geom_for_voronoi = geom
        if densify_distance != 0:
            if densify_distance > 0:
                max_segment_length = densify_distance
            elif _compactness(geom) < 0.001:
                # Very compact/narrow geometry, so densify_distance is not useful
                max_segment_length = 0
            else:
                # Automatically determine length
                average_width = _average_width(geom)
                max_segment_length = abs(densify_distance) * average_width
                factor_increase = (
                    geom.length / max_segment_length
                ) / shapely.get_num_coordinates(geom)
                max_factor_increase = 10
                if factor_increase > max_factor_increase:
                    # Too large increase in number of points, cap to max_factor_increase
                    max_segment_length *= factor_increase / max_factor_increase

            if max_segment_length > 0:
                geom_for_voronoi = shapely.segmentize(geom, max_segment_length)

        # Remove repeated points, as Voronoi does not like them
        try:
            geom_for_voronoi_dedup = shapely.remove_repeated_points(
                geom_for_voronoi, 1e-8
            )
        except shapely.errors.GEOSException as ex:
            if "invalid number of points in linearring" in str(ex).lower():
                # If this error occurs, try set_precision
                logger.warning(
                    f"Error in remove_repeated_points on "
                    f"{format_short(geom_for_voronoi)}: {ex}. Trying set_precision."
                )
                geom_for_voronoi_dedup = shapely.set_precision(geom_for_voronoi, 1e-8)
            else:
                raise

        if geom_for_voronoi_dedup.is_valid:
            geom_for_voronoi = geom_for_voronoi_dedup

        # Calculate voronoi edges
        try:
            voronoi_edges = shapely.voronoi_polygons(geom_for_voronoi, only_edges=True)
        except shapely.errors.GEOSException as ex:
            if "point array must contain" in str(ex).lower():
                # If this error occurs, try set_precision
                logger.warning(
                    f"Error in voronoi_polygons on {format_short(geom_for_voronoi)}: "
                    f"{ex}. Trying set_precision first."
                )
                geom_for_voronoi = shapely.set_precision(geom_for_voronoi, 1e-8)
                voronoi_edges = shapely.voronoi_polygons(
                    geom_for_voronoi, only_edges=True
                )
            else:
                raise

        # Only keep edges that are covered by the original geometry to remove edges
        # going to infinity,...
        # Remark: contains is optimized for prepared geometries <> within -> faster!
        edges = shapely.get_parts(voronoi_edges)
        shapely.prepare(geom)
        edges = edges[shapely.contains(geom, edges)]
        if len(edges) == 1:
            lines = edges[0]
        elif len(edges) > 1:
            lines = shapely.line_merge(shapely.multilinestrings(edges))
        else:
            # No edges within the polygon, so use intersection
            voronoi_clipped = shapely.intersection(geom, voronoi_edges)
            lines = shapely.line_merge(voronoi_clipped)

        # If min_branch_length != 0, remove short branches
        min_branch_length_cur = min_branch_length
        if min_branch_length_cur < 0:
            # If < 0, calculate
            if average_width is None:
                average_width = _average_width(geom)
            min_branch_length_cur = abs(min_branch_length_cur) * average_width
        if min_branch_length_cur > 0:
            lines = _remove_short_branches_notempty(
                line=lines, min_branch_length=min_branch_length_cur
            )

        # Simplify if needed
        if simplifytolerance is not None:
            tol = simplifytolerance
            if simplifytolerance < 0:
                # Automatically determine tol
                if average_width is None:
                    average_width = _average_width(geom)
                tol = abs(simplifytolerance) * average_width
            lines = shapely.simplify(lines, tol)

        if extend:
            lines = _extend_line.extend_line_to_geometry(lines, geom)

        # Return result
        lines = shapely.normalize(lines)
        return lines

    except Exception as ex:
        raise type(ex)(f"Error for geometry {format_short(geom)}: {ex}") from ex


def _average_width(geom: BaseGeometry) -> float:
    """
    Calculate the average width for a polygon.

    Args:
        geom (BaseGeometry): the input polygon

    Returns:
        float: the average width
    """
    return geom.length / 4 - math.sqrt(max((geom.length / 4) ** 2 - geom.area, 0))


def _compactness(geom: BaseGeometry) -> float:
    """
    Calculate the compactness of a polygon.

    Is also called the Polsby-Popper index.

    Args:
        geom (BaseGeometry): the input polygon

    Returns:
        float: the compactness
    """
    return (4 * math.pi * geom.area) / (geom.boundary.length**2)


def _remove_short_branches_notempty(
    line: shapely.MultiLineString | shapely.LineString | None,
    min_branch_length: float,
) -> shapely.MultiLineString | shapely.LineString | None:
    """
    Remove all branches of the input lines shorter than min_branch_length.

    If this leads to a None or empty result, return a valid line anyway.

    Args:
        line (shapely line): input line
        min_branch_length (float): the minimum length of branches to keep.

    Returns:
        Union[shapely.MultiLineString, shapely.LineString, None]: the cleaned line
    """
    # If line already OK or minimum branch length invalid, just return input
    if line is None or isinstance(line, shapely.LineString) or min_branch_length <= 0:
        return line

    # Remove short branches
    line_cleaned = _remove_short_branches(
        line, min_branch_length, remove_one_by_one=False
    )

    # If _remove_short_branches returned an empty result, try again but less agressive
    if line_cleaned is None or line_cleaned.is_empty:
        line_cleaned = _remove_short_branches(
            line, min_branch_length, remove_one_by_one=True
        )

    # If still an empty result, retain original version
    if line_cleaned is None or line_cleaned.is_empty:
        line_cleaned = line

    return line_cleaned


def _remove_short_branches(
    line: shapely.MultiLineString | shapely.LineString | None,
    min_branch_length: float,
    remove_one_by_one: bool,
) -> shapely.MultiLineString | shapely.LineString | None:
    """
    Remove all branches of the input lines shorter than min_branch_length.

    Args:
        line (shapely line): input line
        min_branch_length (float): the minimum length of branches to keep.
        remove_one_by_one (bool): True to remove short branches one by one, with line
            merges in between. This will give a less clean result, but will less often
            result in an empty result.

    Returns:
        Union[shapely.MultiLineString, shapely.LineString, None]: the cleaned line
    """
    # If line already OK or minimum branch length invalid, just return input
    if line is None or isinstance(line, shapely.LineString) or min_branch_length <= 0:
        return line

    # Remove short branches till there are no more short branches
    line_cleaned = shapely.normalize(line)
    while isinstance(line_cleaned, shapely.MultiLineString):
        # Loop over each line to check if we keep it, ordered by length
        lines_rtree = None
        line_parts_to_remove = []
        line_cleaned_parts = shapely.get_parts(line_cleaned)
        linetuples_sorted = sorted(
            enumerate(line_cleaned_parts),
            key=lambda x: shapely.length(x[1]),
        )
        for line_cur_idx, line_cur in linetuples_sorted:
            # If the line is long enough, always keep it
            if line_cur.length >= min_branch_length:
                continue

            # Check for the first and last point whether they touch another edge
            line_cur_coords = shapely.get_coordinates(line_cur)
            # Check first point
            search_point = shapely.Point(line_cur_coords[0])
            if lines_rtree is None:
                lines_rtree = shapely.STRtree(line_cleaned_parts)
            neighbour_idxs = list(lines_rtree.query(search_point))
            startpoint_adjacency = False

            # If only one found, it is itself so nothing adjacent.
            if len(neighbour_idxs) > 1:
                for neighbour_idx in neighbour_idxs:
                    # If the near line is itself, skip
                    if neighbour_idx == line_cur_idx:
                        continue
                    # Check if the near line really intersects
                    if shapely.intersects(
                        line_cleaned_parts[neighbour_idx], search_point
                    ):
                        startpoint_adjacency = True
                        break

            # Check last point
            search_point = shapely.Point(line_cur_coords[-1])
            neighbour_idxs = list(lines_rtree.query(search_point))
            endpoint_adjacency = False

            # If only one found, it is itself so nothing adjacent.
            if len(neighbour_idxs) > 1:
                for neighbour_idx in neighbour_idxs:
                    # If the near line is itself, skip
                    if neighbour_idx == line_cur_idx:
                        continue
                    # Check if the near line really intersects
                    if shapely.intersects(
                        line_cleaned_parts[neighbour_idx], search_point
                    ):
                        endpoint_adjacency = True
                        break

            if startpoint_adjacency is False and endpoint_adjacency is False:
                # Standalone line, keep it
                continue
            elif startpoint_adjacency and endpoint_adjacency:
                # Line between two others, so keep it
                continue
            else:
                # Only either start or end point has an adjacency: short branch,
                # so don't keep.
                line_parts_to_remove.append(line_cur_idx)
                if remove_one_by_one:
                    break

        # Remove the line parts found
        if len(line_parts_to_remove) > 0:
            line_cleaned = shapely.multilinestrings(
                np.delete(line_cleaned_parts, line_parts_to_remove, axis=0)
            )
        else:
            # If no lines were removed anymore in the last pass, we are ready
            break

        # Merge the lines to keep again...
        line_cleaned = shapely.line_merge(line_cleaned)

    return line_cleaned
