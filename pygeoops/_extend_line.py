from typing import Tuple
from shapely import box, Point


def extend_line_by_ratio(
    p1: Tuple[float, float], p2: Tuple[float, float], ratio: float
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Returns the point interpolated along the line by the ratio specified.

    Args:
        p1 (Tuple[float, float]): the first point of the line
        p2 (Tuple[float, float]): the second point of the line
        ratio (float): the ratio to extend the line with. If ratio < 0, the line
            will be extended in the negative direction.

    Returns:
        Tuple[Tuple[float, float], Tuple[float, float]]: the line extended by
            the ratio specified.
    """
    p_extended = (p1[0] + ratio * (p2[0] - p1[0]), p1[1] + ratio * (p2[1] - p1[1]))
    if ratio > 0:
        return (p1, p_extended)
    else:
        return (p_extended, p2)


def extend_line_to_bbox(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    bbox: Tuple[float, float, float, float],
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Extends a line so both points are onto the boundaries of a given bounding
    box.

    Args:
        p1 (Tuple[float, float]): The first point of the line.
        p2 (Tuple[float, float]): The second point of the line.
        bbox (Tuple[float, float, float, float]): A tuple representing the
            boundary of the bounding box to extend to in the format
            (minx, miny, maxx, maxy).

    Returns:
        Tuple[Tuple[float, float], Tuple[float, float]]: The extended line on
            the boundary of the bbox.
    """
    minx, miny, maxx, maxy = bbox
    if p1[0] == p2[0]:  # vertical line
        return ((p1[0], miny), (p1[0], maxy))
    elif p1[1] == p2[1]:  # horizontal line
        return ((minx, p1[1]), (maxx, p1[1]))
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
        return (
            points_sorted_by_distance[0].coords,
            points_sorted_by_distance[1].coords,
        )
