import shapely
from shapely.geometry import LineString

import pygeoops


def longest_line(poly: shapely.geometry.base.BaseGeometry):
    max_len = 0

    # Iterate over each polygon in the multipolygon
    intersection_points = []
    max_len = 0
    for polygon in poly.geoms:
        # Iterate over each point in the polygon
        for point1 in polygon.exterior.coords:
            # Iterate over each point in the polygon again
            for point2 in polygon.exterior.coords:
                # Skip if points are the same
                if point1 == point2:
                    continue

                # Extend the line to cover the mbr of the polygon
                line = pygeoops.line_interpolate_to_bbox(point1, point2, polygon.bounds)

                # Find intersection points between the line and the polygon
                intersection = LineString(polygon.boundary).intersection(line)
                intersection_points.extend(shapely.get_coordinates(intersection))

        # Iterate over intersection points
        for intersection_pt1 in intersection_points:
            for intersection_pt2 in intersection_points:
                if all(intersection_pt1 != intersection_pt2):
                    # Create a line segment
                    line_segment = LineString([intersection_pt1, intersection_pt2])
                    # Check if line segment lies within the polygon
                    if line_segment.within(polygon):
                        length = line_segment.length
                        if length > max_len:
                            max_len = length
                            max_line = line_segment

    return max_line
