import math
import pytest
from shapely import box, LineString, Polygon

import pygeoops


@pytest.mark.parametrize(
    "desc, line, poly, exp_line",
    [
        (
            "each line extension intersects with one point",
            LineString([(4, 3), (5, 5), (6, 5)]),
            box(0, 0, 10, 10),
            LineString([(2.5, 0), (5, 5), (10, 5)]),
        ),
        (
            "one line extension intersects with multiple points",
            LineString([(4, 3), (5, 5), (6, 5)]),
            Polygon(
                [(3, 0), (3, 10), (7, 10), (7, 3), (10, 10), (10, 0), (3, 0)],
            ),
            LineString([(3, 1), (5, 5), (7, 5)]),
        ),
        (
            "one line extension intersects with a point + a line",
            LineString([(4, 3), (5, 5), (6, 5)]),
            Polygon(
                [(3, 0), (3, 10), (7, 10), (7, 5), (8, 5), (10, 10), (10, 0), (3, 0)],
            ),
            LineString([(3, 1), (5, 5), (7, 5)]),
        ),
        (
            "input line is already on the polygon",
            LineString([(3, 1), (5, 5), (7, 5)]),
            Polygon(
                [(3, 0), (3, 10), (7, 10), (7, 5), (8, 5), (10, 10), (10, 0), (3, 0)],
            ),
            LineString([(3, 1), (5, 5), (7, 5)]),
        ),
        (
            "input line is already on the polygon",
            LineString([(4, 3), (5, 5), (6, 5)]),
            box(4, 0, 5, 1),
            LineString([(4, 3), (5, 5), (6, 5)]),
        ),
    ],
)
def test_extend_line_to_polygon(desc, line, poly, exp_line):
    result = pygeoops.extend_line_to_polygon(line, poly)
    assert result == exp_line


@pytest.mark.parametrize(
    "desc, p1, p2, distance, exp_p",
    [
        ("bl-tr, distance 0", (0, 0), (1, 1), 0, ((0, 0), (1, 1))),
        ("bl-tr, distance 1.44", (0, 0), (1, 1), math.sqrt(2), ((0, 0), (2, 2))),
        ("bl-tr, distance 2.88", (0, 0), (1, 1), 2 * math.sqrt(2), ((0, 0), (3, 3))),
        ("horizontal, distance 1", (0, 0), (1, 0), 1, ((0, 0), (2, 0))),
        ("vertical, distance 1", (0, 0), (0, 1), 1, ((0, 0), (0, 2))),
    ],
)
def test_extend_segment_by_distance(desc, p1, p2, distance, exp_p):
    result = pygeoops.extend_segment_by_distance(p1, p2, distance)
    assert result == exp_p


@pytest.mark.parametrize(
    "exp_error, p1, p2, distance",
    [
        ("distance must be >= 0", (0, 0), (1, 1), -1),
        ("lenght of input segment cannot be 0", (0, 0), (0, 0), 1),
    ],
)
def test_extend_segment_by_distance_invalid(exp_error, p1, p2, distance):
    with pytest.raises(ValueError, match=exp_error):
        _ = pygeoops.extend_segment_by_distance(p1, p2, distance)


@pytest.mark.parametrize(
    "desc, p1, p2, ratio, exp_p",
    [
        ("diagonal bl-tr, ratio 0", (0, 0), (1, 1), 0, ((0, 0), (1, 1))),
        ("diagonal bl-tr, ratio 1", (0, 0), (1, 1), 1, ((0, 0), (2, 2))),
        ("diagonal bl-tr, ratio 0.5", (0, 0), (1, 1), 0.5, ((0, 0), (1.5, 1.5))),
        ("diagonal tr-bl, ratio 0", (1, 1), (0, 0), 0, ((1, 1), (0, 0))),
        ("diagonal tr-bl, ratio 1", (1, 1), (0, 0), 1, ((1, 1), (-1, -1))),
        ("diagonal tr-bl, ratio 0.5", (1, 1), (0, 0), 0.5, ((1, 1), (-0.5, -0.5))),
        ("diagonal br-tl, ratio 1", (1, 0), (0, 1), 1, ((1, 0), (-1, 2))),
        ("diagonal tl-br, ratio 1", (0, 1), (1, 0), 1, ((0, 1), (2, -1))),
        ("horizonal, ratio 0", (0, 0), (1, 0), 0, ((0, 0), (1, 0))),
        ("horizonal, ratio 1", (0, 0), (1, 0), 1, ((0, 0), (2, 0))),
        ("horizonal, ratio 0.5", (0, 0), (1, 0), 0.5, ((0, 0), (1.5, 0))),
        ("vertical, ratio 0", (0, 0), (0, 1), 0, ((0, 0), (0, 1))),
        ("vertical, ratio 1", (0, 0), (0, 1), 1, ((0, 0), (0, 2))),
        ("vertical, ratio 0.5", (0, 0), (0, 1), 0.5, ((0, 0), (0, 1.5))),
    ],
)
def test_extend_segment_by_ratio(desc, p1, p2, ratio, exp_p):
    result = pygeoops.extend_segment_by_ratio(p1, p2, ratio)
    assert result == exp_p


@pytest.mark.parametrize(
    "exp_error, p1, p2, ratio",
    [
        ("ratio must be >= 0", (0, 0), (1, 1), -1),
    ],
)
def test_extend_segment_by_ratio_invalid(exp_error, p1, p2, ratio):
    with pytest.raises(ValueError, match=exp_error):
        _ = pygeoops.extend_segment_by_ratio(p1, p2, ratio)


@pytest.mark.parametrize(
    "desc, p1, p2, bbox, exp_line",
    [
        ("diagonal, left-right", (1, 1), (2, 2), (0, 0, 4, 4), ((0, 0), (4, 4))),
        ("diagonal, right-left", (2, 2), (1, 1), (0, 0, 4, 4), ((4, 4), (0, 0))),
        ("horizontal, left-right", (1, 1), (2, 1), (0, 0, 4, 4), ((0, 1), (4, 1))),
        ("horizontal, right-left", (2, 1), (1, 1), (0, 0, 4, 4), ((4, 1), (0, 1))),
        ("vertical, bottom-top", (1, 1), (1, 2), (0, 0, 4, 4), ((1, 0), (1, 4))),
        ("vertical, top-bottom", (1, 2), (1, 1), (0, 0, 4, 4), ((1, 4), (1, 0))),
    ],
)
def test_extend_segment_to_bbox(desc, p1, p2, bbox, exp_line):
    result = pygeoops.extend_segment_to_bbox(p1, p2, bbox)
    assert result == exp_line
