import pytest

from shapely.geometry import LineString, Polygon, MultiPolygon

from pygeoops._buffer_by_m import buffer_by_m
import test_helper


@pytest.mark.parametrize(
    "line_coords, exp_type, exp_parts_relation",
    [
        ([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]], Polygon, None),
        ([[0, 6, 1], [0, 0, 0], [10, 0, 2], [13, 5, 4]], MultiPolygon, "touches"),
        ([[0, 6, 1], [0, 0, -1], [10, 0, 2], [13, 5, 4]], MultiPolygon, "disjoint"),
    ],
)
def test_buffer_by_m(tmp_path, line_coords, exp_type, exp_parts_relation):
    """Test buffer_by_m function.

    Specific cases tested:
    - a normal case with M values all > 0 will produce a single Polygon
    - a case with one M value = 0 will produce a MultiPolygon with touching parts, as
      the point(s) with zero distance will be represented as the original point
    - a case with one M value < 0 will produce a MultiPolygon with disjoint parts, as
      the point(s) with negative distance will be omitted from the buffer
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
            raise ValueError(f"Unknown expected parts relation: {exp_parts_relation}")

    # Plot for visual inspection
    output_path = tmp_path / "test_buffer_by_m.png"
    test_helper.plot([buffer_geom, line], output_path)
