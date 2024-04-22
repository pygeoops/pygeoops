from shapely import MultiPolygon, Polygon

import pygeoops


def test_longestline():
    multipolygon = MultiPolygon(
        [
            Polygon([(7, 10), (8, 11), (9, 11), (8, 10), (7, 9.5), (7, 10)]),
            Polygon([(9.5, 8.5), (10, 9), (10, 10), (11, 9), (9.5, 8.5)]),
        ]
    )

    longest_line = pygeoops.longest_line(multipolygon)
    assert longest_line.length == 2.5
