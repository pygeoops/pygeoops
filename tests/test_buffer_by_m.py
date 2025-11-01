from concurrent.futures import ProcessPoolExecutor

import pytest

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Polygon, MultiPolygon

from pygeoops._buffer_by_m import buffer_by_m
from pygeoops._compat import SHAPELY_GTE_21
import test_helper

if not SHAPELY_GTE_21:
    pytest.skip("buffer_by_m tests require Shapely >= 2.1.0", allow_module_level=True)


@pytest.mark.parametrize(
    "line_coords, exp_type, exp_parts_relation",
    [
        ([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]], Polygon, None),
        ([[0, 6, 1], [0, 0, 0], [10, 0, 2], [13, 5, 4]], MultiPolygon, "touches"),
        ([[0, 6, 1], [0, 0, -1], [10, 0, 2], [13, 5, 4]], MultiPolygon, "disjoint"),
        ([[0, 6, 1], [0, 0, np.nan], [10, 0, 2], [13, 5, 4]], MultiPolygon, "disjoint"),
    ],
)
def test_buffer_by_m(tmp_path, line_coords, exp_type, exp_parts_relation):
    """Test buffer_by_m function.

    Specific cases tested:
    - a normal case with M values all > 0 will produce a single Polygon
    - a case with one M value = 0 will produce a MultiPolygon with touching parts, as
      this point will be represented as the original (unbuffered) point
    - a case with one M value < 0 or NaN will produce a MultiPolygon with disjoint
      parts, as this point will be omitted from the buffer
    """
    line = LineString(line_coords)

    buffer_geom = buffer_by_m(line)

    # Check result
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
    result = buffer_by_m(input)

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


def test_buffer_by_m__no_m_or_z():
    """Test buffer_by_m with LineString without M or Z values."""
    line = LineString([[0, 6], [0, 0], [10, 0], [13, 5]])

    with pytest.raises(ValueError, match="input geometry must have M or Z values"):
        _ = buffer_by_m(line)


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
        results = pool.map(buffer_by_m, input, quad_segs)

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

    buffer_geom = buffer_by_m(line_with_m)

    # Check result
    assert isinstance(buffer_geom, Polygon)
    assert not buffer_geom.is_empty
