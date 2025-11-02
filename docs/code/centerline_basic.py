"""Example of basic usage of the centerline function."""

import matplotlib.pyplot as plt
import shapely
from figures import BLUE, GRAY, W
from shapely.plotting import plot_line, plot_polygon

import pygeoops

fig, ax = plt.subplots(figsize=(W / 2, W / 2), dpi=90)

fancy_t_poly_wkt = (
    "POLYGON ((3 0, 9 0, 7 2, 7 10, 12 10, 12 12, 0 12, 0 10, 5 10, 5 2, 3 0))"
)

# Just a single example
# ---------------------
ax.set_aspect("equal")

poly = shapely.from_wkt(fancy_t_poly_wkt)
centerline = pygeoops.centerline(poly)
plot_polygon(poly, ax=ax, color=GRAY, alpha=0.3, add_points=False)
plot_line(centerline, ax=ax, color=BLUE, alpha=0.7)

plt.show()
