"""Tests for buffer_by_m function."""

import re
from concurrent.futures import ProcessPoolExecutor

import pytest

import geopandas as gpd
import shapely
import numpy as np
from shapely import from_wkt
from shapely.geometry import LineString, Polygon, MultiPolygon

import pygeoops
from pygeoops._compat import GEOS_GTE_3_12_0, SHAPELY_GTE_2_1_0
import test_helper


@pytest.mark.parametrize(
    "line, distance_dim, exp_type, exp_parts_relation",
    [
        (LineString([[0, 6, 1], [0, 0, 2], [9, 0, 2]]), "Z", Polygon, None),
        (LineString([[0, 6, 1], [0, 0, 0], [9, 0, 2]]), "Z", MultiPolygon, "touches"),
        (LineString([[0, 6, 1], [0, 0, -1], [9, 0, 2]]), "Z", MultiPolygon, "disjoint"),
        (
            LineString([[0, 6, 1], [0, 0, np.nan], [9, 0, 2]]),
            "Z",
            MultiPolygon,
            "disjoint",
        ),
        (LineString([[0, 6, -1], [0, 0, -1], [9, 0, -2]]), "Z", Polygon(), None),
        (from_wkt("LINESTRING M (0 6 1, 0 0 2, 9 0 2)"), "M", Polygon, None),
        (from_wkt("LINESTRING M (0 6 -1, 0 0 -1, 9 0 -1)"), "M", Polygon(), None),
        (
            from_wkt("LINESTRING ZM (0 6 -1 1, 0 0 -1 0, 9 0 -1 2)"),
            "M",
            MultiPolygon,
            "touches",
        ),
    ],
)
def test_buffer_by_m(tmp_path, line, distance_dim, exp_type, exp_parts_relation):
    """Test buffer_by_m function with various input geometries.

    Specific cases tested:
    - a normal case with M values all > 0 will produce a single Polygon
    - a case with one M value = 0 will produce a MultiPolygon with touching parts, as
      this point will be represented as the original (unbuffered) point
    - a case with one M value < 0 will produce a MultiPolygon with disjoint
      parts, as this point will be omitted from the buffer
    - a case with one M value = NaN: same as previous case
    - input as WKT LineString M
    - input as WKT LineString M with all negative M values: should produce empty Polygon
    - input as WKT LineString ZM
    """
    if distance_dim == "M" and (not SHAPELY_GTE_2_1_0 or not GEOS_GTE_3_12_0):
        pytest.xfail("Shapely >= 2.1.0 and GEOS >= 3.12.0 required for M values")

    buffer_geom = pygeoops.buffer_by_m(line)

    # Check result
    if exp_type == Polygon():
        # Special case: an empty Polygon is expected as result
        assert buffer_geom.is_empty
        return

    assert isinstance(buffer_geom, exp_type)
    assert not buffer_geom.is_empty

    if exp_parts_relation is not None:
        parts = list(buffer_geom.geoms)
        if exp_parts_relation == "disjoint":
            assert len(parts) == 2
            assert parts[0].disjoint(parts[1])
        elif exp_parts_relation == "touches":
            assert len(parts) == 2
            assert parts[0].touches(parts[1])
        else:
            raise ValueError(f"Unknown {exp_parts_relation=}")

    # Plot for visual inspection
    output_path = tmp_path / "test_buffer_by_m.png"
    test_helper.plot([buffer_geom, line], output_path)


@pytest.mark.skipif(
    SHAPELY_GTE_2_1_0 and GEOS_GTE_3_12_0,
    reason="Shapely >= 2.1.0 and GEOS >= 3.12.0 present, so no error expected",
)
def test_buffer_by_m_dependencies():
    """Test if buffer_by_m gives a proper error when dependencies are not met."""
    line = shapely.from_wkt("LINESTRING M (0 6 1, 0 0 2, 10 0 2, 13 5 4)")
    with pytest.raises(
        ValueError,
        match=re.escape("For M, Shapely >= 2.1.0 and GEOS >= 3.12.0 are needed"),
    ):
        _ = pygeoops.buffer_by_m(line)


@pytest.mark.parametrize("input_type", ["geoseries", "ndarray", "list"])
def test_buffer_by_m_geometries(tmp_path, input_type):
    """Test processing an array of polygons."""
    # Prepare test data
    input = [
        LineString([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]]),
        LineString([[0, 6, 1], [0, 0, 0], [10, 0, 2], [13, 5, 4]]),
        LineString([[0, 6, 1], [0, 0, -1], [10, 0, 2], [13, 5, 4]]),
    ]
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
    result = pygeoops.buffer_by_m(input)

    # Check result
    assert result is not None
    if input_type == "geoseries":
        assert isinstance(result, gpd.GeoSeries)
    else:
        assert isinstance(result, np.ndarray)
    for test_idx, line in enumerate(input):
        output_path = tmp_path / f"{__name__}{line.wkt}.png"
        test_helper.plot(
            [result[start_idx + test_idx], input[start_idx + test_idx]], output_path
        )


def test_buffer_by_m_parallel():
    """Test processing an array of polygons."""
    # Prepare test data
    input = [
        LineString([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]]),
        LineString([[0, 6, 1], [0, 0, 0], [10, 0, 2], [13, 5, 4]]),
        LineString([[0, 6, 1], [0, 0, -1], [10, 0, 2], [13, 5, 4]]),
    ]
    exp_type = [Polygon, MultiPolygon, MultiPolygon]
    exp_parts_relation = [None, "touches", "disjoint"]

    # Run test
    quad_segs = [4] * len(input)
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = pool.map(pygeoops.buffer_by_m, input, quad_segs)

    # Check result
    for line, buffer_geom, exp_type, exp_parts_relation in zip(
        input, results, exp_type, exp_parts_relation
    ):
        assert buffer_geom is not None
        assert not buffer_geom.is_empty
        assert isinstance(buffer_geom, exp_type)
        if exp_parts_relation is not None:
            parts = list(buffer_geom.geoms)
            if exp_parts_relation == "disjoint":
                assert parts[0].disjoint(parts[1])
            elif exp_parts_relation == "touches":
                assert parts[0].touches(parts[1])
            else:
                raise ValueError(f"Unknown {exp_parts_relation=}")


def test_buffer_by_m_separate_distances():
    """Test buffer_by_m with LineString without M or Z values."""
    line = LineString([[0, 6], [0, 0], [10, 0], [13, 5]])
    distances = [1, 2, 2, 4]
    line_with_m = LineString([[x, y, m] for (x, y), m in zip(line.coords, distances)])

    buffer_geom = pygeoops.buffer_by_m(line_with_m)

    # Check result
    assert isinstance(buffer_geom, Polygon)
    assert not buffer_geom.is_empty


def test_buffer_by_m_without_zm():
    """Test buffer_by_m with LineString without M or Z values."""
    line = LineString([[0, 6], [0, 0], [10, 0], [13, 5]])

    with pytest.raises(ValueError, match="input geometry must have M or Z values"):
        _ = pygeoops.buffer_by_m(line)
