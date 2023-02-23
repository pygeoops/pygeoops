# -*- coding: utf-8 -*-
"""
Tests for centerline.
"""

from pathlib import Path
import pytest
import shapely
from shapely.geometry.base import BaseGeometry
import shapely.plotting

import pygeoops
import test_helper

# Define the box tests here so they can be used in both the box test + the array test.
box_tests = [
    (
        "input: rectangle, output: line",
        "POLYGON ((0 0, 0 2, 10 2, 10 0, 0 0))",
        "LINESTRING (1 1, 9 1)",
    ),
    (
        "input: square, output: cross",
        "POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
        "MULTILINESTRING ((5 5, 10 5), (5 5, 5 10), (5 0, 5 5), (0 5, 5 5))",
    ),
]


@pytest.mark.parametrize("test, poly_wkt, expected_centerline_wkt", box_tests)
def test_centerline_box(
    tmp_path: Path, test: str, poly_wkt: str, expected_centerline_wkt: str
):
    """Some test with simple boxes."""
    poly = shapely.from_wkt(poly_wkt)
    centerline = pygeoops.centerline(poly)
    assert centerline is not None
    assert isinstance(centerline, BaseGeometry)
    output_path = tmp_path / f"test_centerline_box_{test}.png"
    test_helper.plot([poly, centerline], output_path)
    assert centerline.wkt == expected_centerline_wkt, f"test descr: {test}"


def test_centerline_box_arr(tmp_path: Path):
    """Test processing an array of polygons."""
    polys = [shapely.from_wkt(box_tests[0][1]), shapely.from_wkt(box_tests[1][1])]
    centerlines = pygeoops.centerline(polys)
    assert centerlines is not None
    for test_idx, box_test in enumerate(box_tests):
        output_path = tmp_path / f"test_centerline_box_arr_{box_test[0]}.png"
        test_helper.plot([centerlines[test_idx], centerlines[test_idx]], output_path)
        assert centerlines[test_idx].wkt == box_test[2]


@pytest.mark.parametrize(
    "test, poly_wkt, expected_centerline_wkt",
    [
        (
            "input: L shape, output: L line",
            "POLYGON ((0 0, 0 10, 2 10, 2 2, 10 2, 10 0, 0 0))",
            "LINESTRING (1 9, 1 1, 9 1)",
        ),
        (
            "input: fancy L shape, output: L-ish line",
            "POLYGON ((0 0, 0 8, -2 10, 4 10, 2 8, 2 2, 10 2, 10 0, 0 0))",
            "MULTILINESTRING ((1 8.8, 1.1 1.1, 8.9 1), (1 8.8, 3.3 9.8), (-1.2 9.8, 1 8.8))",  # noqa: E501
        ),
    ],
)
def test_centerline_poly(
    tmp_path: Path, test: str, poly_wkt: str, expected_centerline_wkt: str
):
    """More complicated polygon tests."""
    poly = shapely.from_wkt(poly_wkt)
    centerline = pygeoops.centerline(poly)
    assert centerline is not None
    assert isinstance(centerline, BaseGeometry)
    # Reduce precision to get simplified expected centerline
    centerline = shapely.set_precision(centerline, 0.1)
    output_path = tmp_path / f"test_centerline_box_{test}.png"
    test_helper.plot([poly, centerline], output_path)
    assert centerline.wkt == expected_centerline_wkt, f"test descr: {test}"
