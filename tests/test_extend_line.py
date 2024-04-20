import pytest

import pygeoops


@pytest.mark.parametrize(
    "p1, p2, ratio, exp_p",
    [
        ((0, 0), (1, 1), 1, ((0, 0), (1, 1))),
        ((0, 0), (1, 1), 2, ((0, 0), (2, 2))),
        ((0, 0), (1, 1), 0.5, ((0, 0), (0.5, 0.5))),
        ((0, 0), (1, 1), -1, ((-1, -1), (1, 1))),
        ((0, 0), (1, 1), -2, ((-2, -2), (1, 1))),
        ((0, 0), (1, 1), -0.5, ((-0.5, -0.5), (1, 1))),
    ],
)
def test_extend_line_by_ratio(p1, p2, ratio, exp_p):
    result = pygeoops.extend_line_by_ratio(p1, p2, ratio)
    assert result == exp_p


@pytest.mark.parametrize(
    "p1, p2, bbox, exp_line",
    [
        ((1, 1), (2, 2), (0, 0, 4, 4), ((0, 0), (4, 4))),
        ((1, 1), (2, 1), (0, 0, 4, 4), ((0, 1), (4, 1))),
        ((1, 1), (1, 2), (0, 0, 4, 4), ((1, 0), (1, 4))),
    ],
)
def test_extend_line_to_bbox(p1, p2, bbox, exp_line):
    result = pygeoops.extend_line_to_bbox(p1, p2, bbox)
    assert result == exp_line
