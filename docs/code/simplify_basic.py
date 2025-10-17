import matplotlib.pyplot as plt
import shapely
from shapely import LineString
from shapely.plotting import plot_line, plot_polygon

import pygeoops

from figures import W, BLACK, BLUE, GRAY, YELLOW

fig, ax = plt.subplots(figsize=(W / 2, W / 3), dpi=90)

poly_wkt = (
    "POLYGON ((0 5, 0 6, 1 6, 1 7, 2 7, 2 8, 3 8, 3 9, 4 9, 4 10, 5 10, 5 9, "
    "6 9, 6 8, 7 8, 7 7, 8 7, 8 6, 9 6, 9 5, 0 5))"
)

# Just a single example
# ---------------------
ax.set_aspect("equal")

poly = shapely.from_wkt(poly_wkt)
simplified = pygeoops.simplify(poly, tolerance=1.0)
plot_polygon(poly, ax=ax, color=GRAY, alpha=0.5, add_points=False)
plot_polygon(simplified, ax=ax, alpha=0.3, color=BLUE, linewidth=3)

plt.show()
