from typing import Tuple
from shapely import LineString, box, Point


def line_interpolate_point(
    p1: Tuple[float, float], p2: Tuple[float, float], ratio: float
) -> Tuple[float, float]:
    """
    Returns the point interpolated along the line by the ratio specified.

    Args:
        p1 (Tuple[float, float]): the first point of the line
        p2 (Tuple[float, float]): the second point of the line
        ratio (float): the ratio to intrapolate the line with. If ratio < 0, the line
            will be intrapolated in the negative direction.

    Returns:
        Tuple[float, float]: the point along the extrapolated line.
    """
    p_intrapolated = (p1[0] + ratio * (p2[0] - p1[0]), p1[1] + ratio * (p2[1] - p1[1]))
    return p_intrapolated


def line_interpolate_to_bbox(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    bbox: Tuple[float, float, float, float],
) -> LineString:
    """
    Interpolates a line so both points are onto the boundaries of a given bounding box.

    Args:
        p1 (Tuple[float, float]): The first point of the line.
        p2 (Tuple[float, float]): The second point of the line.
        bbox (Tuple[float, float, float, float]): A tuple representing the boundary of
            the bounding box to interpolate to in the format (minx, miny, maxx, maxy).

    Returns:
        LineString: The interpolated line on the boundary of the bbox.
    """
    minx, miny, maxx, maxy = bbox
    if p1[0] == p2[0]:  # vertical line
        return LineString([(p1[0], miny), (p1[0], maxy)])
    elif p1[1] == p2[1]:  # horizontal line
        return LineString([(minx, p1[1]), (maxx, p1[1])])
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
        bbox_geom = box(minx, miny, maxx, maxy)
        points_sorted_by_distance = sorted(
            points_on_boundary_lines, key=bbox_geom.distance
        )
        return LineString(points_sorted_by_distance[:2])
