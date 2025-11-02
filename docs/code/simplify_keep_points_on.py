"""Example of using the 'keep_points_on' parameter in the simplify function."""

import matplotlib.pyplot as plt
import shapely
from figures import BLUE, GRAY, W
from shapely.plotting import plot_polygon

import pygeoops

fig, (ax1, ax2) = plt.subplots(
    nrows=1, ncols=2, figsize=(W, W / 3), dpi=90, layout="constrained"
)

poly_wkt = (
    "POLYGON ((0 5, 0 6, 1 6, 1 7, 2 7, 2 8, 3 8, 3 9, 4 9, 4 10, 5 10, 5 9, "
    "6 9, 6 8, 7 8, 7 7, 8 7, 8 6, 9 6, 9 5, 0 5))"
)

# 1: default simplification
# -------------------------
ax1.set_title("a) default")
ax1.set_aspect("equal")

poly = shapely.from_wkt(poly_wkt)
simplified = pygeoops.simplify(poly, tolerance=1.0)
plot_polygon(poly, ax=ax1, color=GRAY, alpha=0.3, add_points=False)
plot_polygon(simplified, ax=ax1, alpha=0.3, color=BLUE, linewidth=3)

# 2: keep_points_on=poly.envelope.boundary
# ----------------------------------------
ax2.set_title("b) keep_points_on=poly.envelope.boundary")
ax2.set_aspect("equal")

poly = shapely.from_wkt(poly_wkt)
simplified = pygeoops.simplify(
    poly, tolerance=1.0, keep_points_on=poly.envelope.boundary
)
plot_polygon(poly, ax=ax2, color=GRAY, alpha=0.3, add_points=False)
plot_polygon(simplified, ax=ax2, alpha=0.3, color=BLUE, linewidth=3)

plt.show()
