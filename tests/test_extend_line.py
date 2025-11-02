import math
import re

import pytest
import test_helper
from shapely import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
    box,
    get_coordinates,
)

import pygeoops
from pygeoops import _extend_line


@pytest.mark.parametrize(
    "desc, line, start_distance, end_distance, exp_line",
    [
        (
            "line with 1 diagonal segment, start_distance != end_distance",
            LineString([(1, 1), (2, 2)]),
            math.sqrt(2),
            2 * math.sqrt(2),
            LineString([(0, 0), (4, 4)]),
        ),
        (
            "line with 1 diagonal segment, start_distance = end_distance",
            LineString([(1, 1), (2, 2)]),
            math.sqrt(2),
            math.sqrt(2),
            LineString([(0, 0), (3, 3)]),
        ),
        (
            "line with 3 segments, start and end vertical",
            LineString([(2, 3), (2, 2), (3, 2), (3, 1)]),
            1,
            2,
            LineString([(2, 4), (2, 2), (3, 2), (3, -1)]),
        ),
        (
            "0 start_distance and end_distance",
            LineString([(1, 1), (2, 2)]),
            0,
            0,
            LineString([(1, 1), (2, 2)]),
        ),
    ],
)
def test_extend_line_by_distance(desc, line, start_distance, end_distance, exp_line):
    result = pygeoops.extend_line_by_distance(line, start_distance, end_distance)
    assert result == exp_line


@pytest.mark.parametrize(
    "error, line, geom",
    [
        (
            "geometry must be a (Multi)Polygon (Multi)LineString",
            LineString([(3, 5), (5, 5)]),
            Point(0, 0),
        ),
        (
            "line must be (Multi)LineString",
            Point(0, 0),
            LineString([(3, 5), (5, 5)]),
        ),
    ],
)
def test_extend_line_to_geometry_error(error, line, geom):
    with pytest.raises(ValueError, match=re.escape(error)):
        _ = pygeoops.extend_line_to_geometry(line, geom)


@pytest.mark.parametrize(
    "desc, line, geom, exp_line",
    [
        (
            "input multiline, Y shape, 2 point linestrings",
            MultiLineString([[(3, 5), (5, 5)], [(5, 5), (7, 7)], [(5, 5), (7, 3)]]),
            box(0, 0, 10, 10),
            MultiLineString([[(0, 5), (5, 5)], [(5, 5), (10, 10)], [(5, 5), (10, 0)]]),
        ),
        (
            "input multiline, Y shape, 3 point linestrings",
            MultiLineString(
                [
                    [(3, 5), (4, 5), (5, 5)],
                    [(5, 5), (6, 6), (7, 7)],
                    [(5, 5), (6, 4), (7, 3)],
                ]
            ),
            box(0, 0, 10, 10),
            MultiLineString(
                [
                    [(0, 5), (4, 5), (5, 5)],
                    [(5, 5), (6, 6), (10, 10)],
                    [(5, 5), (6, 4), (10, 0)],
                ]
            ),
        ),
        (
            "input multiline, 3 parallel linestrings",
            MultiLineString([[(3, 5), (5, 5)], [(3, 3), (5, 3)], [(3, 7), (5, 7)]]),
            box(0, 0, 10, 10),
            MultiLineString([[(0, 5), (10, 5)], [(0, 3), (10, 3)], [(0, 7), (10, 7)]]),
        ),
    ],
)
def test_extend_line_to_geometry_multiline(desc, line, geom, exp_line):
    result = pygeoops.extend_line_to_geometry(line, geom)
    assert result == exp_line


@pytest.mark.parametrize(
    "desc, line, geom, exp_line",
    [
        (
            "input multiline, 2 linestrings in 2 polygons",
            MultiLineString([[(3, 5), (5, 5)], [(23, 5), (25, 5)]]),
            MultiPolygon([box(0, 0, 10, 10), box(20, 0, 30, 10)]),
            MultiLineString([[(0, 5), (10, 5)], [(20, 5), (30, 5)]]),
        ),
    ],
)
def test_extend_line_to_geometry_multipolygon(desc, line, geom, exp_line):
    result = pygeoops.extend_line_to_geometry(line, geom)
    assert result == exp_line


@pytest.mark.parametrize(
    "desc, line, geom, exp_line",
    [
        (
            "each line extension intersects with one polygon boundary",
            LineString([(4, 3), (5, 5), (6, 5)]),
            box(0, 0, 10, 10),
            LineString([(2.5, 0), (5, 5), (10, 5)]),
        ),
        (
            "each line extension intersects with one line boundary",
            LineString([(4, 5), (5, 5), (6, 5)]),
            MultiLineString([[(0, 0), (0, 10)], [(10, 0), (10, 10)]]),
            LineString([(0, 5), (5, 5), (10, 5)]),
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
def test_extend_line_to_geometry_singleline(tmp_path, desc, line, geom, exp_line):
    result = pygeoops.extend_line_to_geometry(line, geom)
    output_path = tmp_path / "test_extend_line_to_geometry_singleline.png"
    test_helper.plot([geom, result], output_path)
    assert result == exp_line


@pytest.mark.parametrize(
    "desc, line, geom, exp_line",
    [
        (
            "input multiline, Y shape, 2 point linestrings",
            MultiLineString([[(3, 5), (5, 5)], [(5, 5), (7, 7)], [(5, 5), (7, 3)]]),
            Polygon(
                get_coordinates(box(0, 0, 10, 10)), [get_coordinates(box(5, 4, 6, 6))]
            ),
            MultiLineString([[(0, 5), (5, 5)], [(5, 5), (10, 10)], [(5, 5), (10, 0)]]),
        ),
        (
            "input multiline, Y shape, 3 point linestrings",
            MultiLineString(
                [
                    [(3, 5), (4, 5), (5, 5)],
                    [(5, 5), (6, 6), (7, 7)],
                    [(5, 5), (6, 4), (7, 3)],
                ]
            ),
            Polygon(
                get_coordinates(box(0, 0, 10, 10)), [get_coordinates(box(5, 4, 6, 6))]
            ),
            MultiLineString(
                [
                    [(0, 5), (4, 5), (5, 5)],
                    [(5, 5), (6, 6), (10, 10)],
                    [(5, 5), (6, 4), (10, 0)],
                ]
            ),
        ),
        (
            "input multiline, 3 parallel linestrings",
            MultiLineString([[(3, 5), (5, 5)], [(3, 3), (5, 3)], [(3, 7), (5, 7)]]),
            Polygon(
                get_coordinates(box(0, 0, 10, 10)), [get_coordinates(box(6, 4, 7, 6))]
            ),
            MultiLineString([[(0, 5), (6, 5)], [(0, 3), (10, 3)], [(0, 7), (10, 7)]]),
        ),
    ],
)
def test_extend_line_to_polygon_island(tmp_path, desc, line, geom, exp_line):
    result = pygeoops.extend_line_to_geometry(line, geom)
    output_path = tmp_path / "test_extend_line_to_geometry_island.png"
    test_helper.plot([geom, result], output_path)
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
    result = _extend_line._extend_segment_by_distance(p1, p2, distance)
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
        _ = _extend_line._extend_segment_by_distance(p1, p2, distance)


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
    result = _extend_line._extend_segment_by_ratio(p1, p2, ratio)
    assert result == exp_p


@pytest.mark.parametrize(
    "exp_error, p1, p2, ratio",
    [
        ("ratio must be >= 0", (0, 0), (1, 1), -1),
    ],
)
def test_extend_segment_by_ratio_invalid(exp_error, p1, p2, ratio):
    with pytest.raises(ValueError, match=exp_error):
        _ = _extend_line._extend_segment_by_ratio(p1, p2, ratio)


@pytest.mark.parametrize(
    "desc, p1, p2, bbox, exp_line",
    [
        ("diag, left-right", (1, 1), (2, 2), (0, 0, 4, 4), ((0, 0), (4, 4))),
        ("diag, left-right, switched", (1, 1), (2, 2), (4, 4, 0, 0), ((0, 0), (4, 4))),
        ("diag, left-right, touch", (2, 2), (4, 4), (0, 0, 4, 4), ((0, 0), (4, 4))),
        ("diag, right-left", (2, 2), (1, 1), (0, 0, 4, 4), ((4, 4), (0, 0))),
        ("diag, right-left, touch", (4, 4), (2, 2), (0, 0, 4, 4), ((4, 4), (0, 0))),
        ("diag, right-left, beyond", (5, 5), (2, 2), (0, 0, 4, 4), ((4, 4), (0, 0))),
        ("horizontal, left-right", (1, 1), (2, 1), (0, 0, 4, 4), ((0, 1), (4, 1))),
        ("horizontal, right-left", (2, 1), (1, 1), (0, 0, 4, 4), ((4, 1), (0, 1))),
        ("vertical, bottom-top", (1, 1), (1, 2), (0, 0, 4, 4), ((1, 0), (1, 4))),
        ("vertical, top-bottom", (1, 2), (1, 1), (0, 0, 4, 4), ((1, 4), (1, 0))),
    ],
)
def test_extend_segment_to_bbox(desc, p1, p2, bbox, exp_line):
    result = _extend_line._extend_segment_to_bbox(p1, p2, bbox)
    assert result == exp_line
