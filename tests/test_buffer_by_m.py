from shapely.geometry import LineString, MultiPolygon

from pygeoops._buffer_by_m import buffer_by_m


def test_buffer_by_m():
    line_coords = [
        [0, 0, 3],
        [5, -2, 4],
        [10, 2, 0],
        [15, 0, 2],
        [20, 5, 5],
        [25, 0, 2],
        [35, 0, 2],
    ]
    line = LineString(line_coords)

    buffer_geom = buffer_by_m(line)

    assert isinstance(buffer_geom, MultiPolygon)
    assert not buffer_geom.is_empty
