import math
import shapely
from shapely import box, LineString, Polygon, Point


def extend_line_by_distance(
    line: LineString, start_distance: float, end_distance: float
) -> LineString:
    """
    Extends a line with the specified distances.

    Args:
        line (LineString): The line to extend.
        start_distance (float): The distance to extend the start of the line
            with.
        end_distance (float): The distance to extend the end of the line with.

    Returns:
        LineString: The extended line.
    """
    if start_distance == 0 and end_distance == 0:
        return line

    line_coords = shapely.get_coordinates(line)
    line_result = line_coords.copy()

    # Extend the start and end of the line
    _, line_result[0] = _extend_segment_by_distance(
        line_coords[1], line_coords[0], start_distance
    )
    _, line_result[-1] = _extend_segment_by_distance(
        line_coords[-2], line_coords[-1], end_distance
    )

    return LineString(line_result)


def extend_line_to_polygon(line: LineString, geometry: Polygon) -> LineString:
    """
    Extends a line to a given Polygon.

    Args:
        line (LineString): The line to extend.
        geometry (Polygon): The Polygon to extend the line to.

    Returns:
        LineString: The extended line.
    """
    line_coords = shapely.get_coordinates(line)
    line_result = line_coords.copy()
    geometry_line = LineString(shapely.get_coordinates(geometry))
    shapely.prepare(geometry_line)

    # Find the closest point on geometry_line that the start of the line can extend to.
    line_result[0] = _find_closest_extend_point(
        line_coords[1], line_coords[0], geometry_line
    )

    # Find the closest point on geometry_line that the end of the line can extend to.
    line_result[-1] = _find_closest_extend_point(
        line_coords[-2], line_coords[-1], geometry_line
    )

    return LineString(line_result)


def _find_closest_extend_point(
    p1: tuple[float, float],
    p2: tuple[float, float],
    geometry_line: LineString,
) -> tuple[float, float]:
    """
    Find the closest point on the geometry line that can be extended to.

    Args:
        p1 (Tuple[float, float]): point 1 of the segment to extend.
        p2 (Tuple[float, float]): point 2 of the segment to extend.
        geometry_line (LineString): the line to extend to.

    Returns:
        Tuple[float, float]: the closest point on the geometry_line that can be
            extended to.
    """
    # If p2 is already on the geometry line, return p2.
    if geometry_line.intersects(Point(p2)):
        return p2

    # Extend the segment to the bounding box of the geometry.
    _, p2_ext = _extend_segment_to_bbox(p1, p2, bbox=geometry_line.bounds)

    # We want to find the intersection point of the extension with the geometry lines
    # that is closest to p2.
    end_extension = (p2, p2_ext)
    intersections = geometry_line.intersection(LineString(end_extension))
    intersection_points = shapely.get_coordinates(intersections)

    if len(intersection_points) == 0:
        # No intersection found, so return input point p2.
        return p2
    else:
        # Find the intersection point closest to input point p2.
        intersection_points = shapely.points(intersection_points)
        p2_point = Point(p2)
        points_sorted_by_distance = sorted(intersection_points, key=p2_point.distance)
        return points_sorted_by_distance[0].coords[0]


def _extend_segment_by_distance(
    p1: tuple[float, float], p2: tuple[float, float], distance: float
) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Extends the segment by the distance specified.

    Args:
        p1 (Tuple[float, float]): the first point of the segment
        p2 (Tuple[float, float]): the second point of the segment
        distance (float): the distance to extend the segment with. If distance
            < 0, the segment will be extended in the negative direction.

    Returns:
        Tuple[Tuple[float, float], Tuple[float, float]]: the segment extended by
            the distance specified.
    """
    if distance < 0:
        raise ValueError(f"distance must be >= 0, received: {distance}")

    segment_length = math.sqrt(pow(p1[0] - p2[0], 2.0) + pow(p1[1] - p2[1], 2.0))
    if segment_length == 0:
        raise ValueError("lenght of input segment cannot be 0")
    ratio = distance / segment_length
    return _extend_segment_by_ratio(p1, p2, ratio=ratio)


def _extend_segment_by_ratio(
    p1: tuple[float, float], p2: tuple[float, float], ratio: float
) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Extends the segment by a ratio.

    Args:
        p1 (Tuple[float, float]): the first point of the segment
        p2 (Tuple[float, float]): the second point of the segment
        ratio (float): the ratio to extend the segment with. Ratio must be >= 0.

    Returns:
        Tuple[Tuple[float, float], Tuple[float, float]]: the segment extended by
            the ratio specified.
    """
    if ratio < 0:
        raise ValueError(f"ratio must be >= 0, received: {ratio}")

    x_ext = p2[0] + (p2[0] - p1[0]) * ratio
    y_ext = p2[1] + (p2[1] - p1[1]) * ratio
    p_ext = (x_ext, y_ext)

    return (p1, p_ext)


def _extend_segment_to_bbox(
    p1: tuple[float, float],
    p2: tuple[float, float],
    bbox: tuple[float, float, float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Extends a segment so both points are on the boundaries of a given bounding box.

    Args:
        p1 (Tuple[float, float]): The first point of the segment.
        p2 (Tuple[float, float]): The second point of the segment.
        bbox (Tuple[float, float, float, float]): A tuple representing the
            boundary of the bounding box to extend to in the format
            (minx, miny, maxx, maxy).

    Returns:
        Tuple[Tuple[float, float], Tuple[float, float]]: The extended segment on
            the boundary of the bbox.
    """
    minx, miny, maxx, maxy = bbox
    if p1[0] == p2[0]:  # vertical segment
        if p1[1] < p2[1]:
            # Keep segment from bottom to top
            return ((p1[0], miny), (p1[0], maxy))
        else:
            # Keep segment from top to bottom
            return ((p1[0], maxy), (p1[0], miny))
    elif p1[1] == p2[1]:  # horizontal segment
        if p1[0] < p2[0]:
            # Keep segment from left to right
            return ((minx, p1[1]), (maxx, p1[1]))
        else:
            # Keep segment from right to left
            return ((maxx, p1[1]), (minx, p1[1]))
    else:
        # linear equation: y = k*x + m
        k = (p2[1] - p1[1]) / (p2[0] - p1[0])
        m = p1[1] - k * p1[0]
        y0 = k * minx + m
        y1 = k * maxx + m
        x0 = (miny - m) / k
        x1 = (maxy - m) / k
        points_on_boundary_lines = [
            Point(minx, y0),
            Point(maxx, y1),
            Point(x0, miny),
            Point(x1, maxy),
        ]
        # Sort the points to the points found closest to the bbox are first
        bbox_geom = box(minx, miny, maxx, maxy)
        points_sorted_by_distance = sorted(
            points_on_boundary_lines, key=bbox_geom.distance
        )

        # Make sure the point belonging to the first input param is first in result.
        p_extended1 = next(iter(points_sorted_by_distance[0].coords))
        p_extended2 = next(iter(points_sorted_by_distance[1].coords))
        if p1[0] < p2[0]:
            if p_extended1[0] < p_extended2[0]:
                return (p_extended1, p_extended2)
            else:
                return (p_extended2, p_extended1)
        else:
            if p_extended1[0] > p_extended2[0]:
                return (p_extended1, p_extended2)
            else:
                return (p_extended2, p_extended1)
