# -*- coding: utf-8 -*-
"""
Tests for centerline.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
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
        "input: square, output: line",
        "POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
        "LINESTRING (5 0, 5 10)",
    ),
]


@pytest.mark.parametrize("test, poly_wkt, expected_centerline_wkt", box_tests)
@pytest.mark.parametrize("input_0dim_array", [True, False])
def test_centerline_box(
    tmp_path: Path,
    test: str,
    poly_wkt: str,
    input_0dim_array: bool,
    expected_centerline_wkt: str,
):
    """Some test with simple boxes."""
    poly = shapely.from_wkt(poly_wkt)

    # Test
    if input_0dim_array:
        centerline = pygeoops.centerline(np.array(poly))
    else:
        centerline = pygeoops.centerline(poly)
    assert centerline is not None
    assert isinstance(centerline, BaseGeometry)
    output_path = tmp_path / f"test_centerline_box_{test}.png"
    test_helper.plot([poly, centerline], output_path)
    assert centerline.wkt == expected_centerline_wkt, f"test descr: {test}"


@pytest.mark.parametrize("input_type", ["geoseries", "ndarray", "list"])
def test_centerline_box_geometries(tmp_path: Path, input_type):
    """Test processing an array of polygons."""
    # Prepare test data
    input = [shapely.from_wkt(box_tests[0][1]), shapely.from_wkt(box_tests[1][1])]

    start_idx = 0
    if input_type == "geoseries":
        # For geoseries, also check if the indexers are retained!
        start_idx = 5
        input = gpd.GeoSeries(
            input, index=[index + start_idx for index in range(len(input))]
        )
    elif input_type == "ndarray":
        input = np.array(input)  # type: ignore[assignment]

    # Run test
    result = pygeoops.centerline(input)

    # Check result
    assert result is not None
    if input_type == "geoseries":
        assert isinstance(result, gpd.GeoSeries)
    else:
        assert isinstance(result, np.ndarray)
    for test_idx, box_test in enumerate(input):
        output_path = tmp_path / f"{__name__}{box_test.wkt}.png"
        test_helper.plot(
            [result[start_idx + test_idx], input[start_idx + test_idx]], output_path
        )
        assert result[start_idx + test_idx].wkt == box_tests[test_idx][2]


def test_centerline_None_geometry():
    assert pygeoops.centerline(None) is None


@pytest.mark.parametrize(
    "test, min_branch_length, poly_wkt, expected_centerline_wkt",
    [
        (
            "input: elleptical shape, resulted in small branch not being removed",
            0.0,
            "MULTIPOLYGON (((0 1, 1 3.25, 2 4.5, 3 5.75, 3.5 6.25, 5 3.25, 3.75 1.75, 2.5 0.5, 1 0, 0 1)))",  # noqa: E501
            "MULTILINESTRING ((3.2641509433962264 3.3726415094339623, 3.7916666666666665 5.458333333333333), (3.2641509433962264 3.3726415094339623, 3.34375 3.359375), (1.375 1.375, 3.2641509433962264 3.3726415094339623))",  # noqa: E501
        ),
        (
            "input: elleptical shape, resulted in small branch not being removed",
            -1.0,
            "MULTIPOLYGON (((0 1, 1 3.25, 2 4.5, 3 5.75, 3.5 6.25, 5 3.25, 3.75 1.75, 2.5 0.5, 1 0, 0 1)))",  # noqa: E501
            "LINESTRING (1.375 1.375, 3.7916666666666665 5.458333333333333)",
        ),
        (
            "input: fancy L shape, output: L-ish line",
            0.0,
            "POLYGON ((0 0, 0 8, -2 10, 4 10, 2 8, 2 2, 10 2, 10 0, 0 0))",
            "MULTILINESTRING ((8.87687074829932 0.9829931972789112, 9.2 1.5), (8.87687074829932 0.9829931972789112, 9.166666666666666 0.5), (1.1367816091954022 1.1160919540229888, 8.87687074829932 0.9829931972789112), (1 8.75, 3.25 9.75), (1 8.75, 1.1367816091954022 1.1160919540229888), (0.833333333333333 0.8, 1.1367816091954022 1.1160919540229888), (-1.25 9.75, 1 8.75))",  # noqa: E501
        ),
        (
            "input: fancy L shape, output: L-ish line",
            -1.0,
            "POLYGON ((0 0, 0 8, -2 10, 4 10, 2 8, 2 2, 10 2, 10 0, 0 0))",
            "MULTILINESTRING ((1 8.75, 1.1367816091954022 1.1160919540229888, 8.87687074829932 0.9829931972789112), (1 8.75, 3.25 9.75), (-1.25 9.75, 1 8.75))",  # noqa: E501
        ),
        (
            "input: L shape, output: L line",
            -1.0,
            "POLYGON ((0 0, 0 10, 2 10, 2 2, 10 2, 10 0, 0 0))",
            "LINESTRING (1 9, 1 1, 9 1)",
        ),
    ],
)
def test_centerline_poly(
    tmp_path: Path,
    test: str,
    min_branch_length: float,
    poly_wkt: str,
    expected_centerline_wkt: str,
):
    """More complicated polygon tests."""
    poly = shapely.from_wkt(poly_wkt)
    centerline = pygeoops.centerline(poly, min_branch_length=min_branch_length)
    assert centerline is not None
    assert isinstance(centerline, BaseGeometry)
    output_path = tmp_path / f"test_centerline_poly_{test}_{min_branch_length}.png"
    test_helper.plot([poly, centerline], output_path)
    assert (
        centerline.wkt == expected_centerline_wkt
    ), f"test descr: {test}, {min_branch_length}"
