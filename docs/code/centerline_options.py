import matplotlib.pyplot as plt
import shapely
from shapely import LineString
from shapely.plotting import plot_line, plot_polygon

import pygeoops

from figures import W, BLACK, BLUE, GRAY, YELLOW

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
    nrows=2, ncols=2, figsize=(W, W), dpi=90, layout="constrained"
)

fancy_t_poly_wkt = (
    "POLYGON ((3 0, 9 0, 7 2, 7 10, 12 10, 12 12, 0 12, 0 10, 5 10, 5 2, 3 0))"
)

# 1: fancy L shape, extend=False
# ------------------------------
ax1.set_title("a) default")
ax1.set_aspect("equal")

poly = shapely.from_wkt(fancy_t_poly_wkt)
centerline = pygeoops.centerline(poly)
plot_polygon(poly, ax=ax1, color=GRAY, alpha=0.3, add_points=False)
plot_line(centerline, ax=ax1, color=BLUE, alpha=0.7)

# 2: fancy L shape, extend=True
# -----------------------------
ax2.set_title("b) extend=True")
ax2.set_aspect("equal")

poly = shapely.from_wkt(fancy_t_poly_wkt)
centerline = pygeoops.centerline(poly, extend=True)
plot_polygon(poly, ax=ax2, color=GRAY, alpha=0.3, add_points=False)
plot_line(centerline, ax=ax2, color=BLUE, alpha=0.7)

# 3: fancy L shape, min_branch_length=-2, extend=False
# ----------------------------------------------------
ax3.set_title("c) min_branch_length=-2")
ax3.set_aspect("equal")

poly = shapely.from_wkt(fancy_t_poly_wkt)
centerline = pygeoops.centerline(poly, extend=False, min_branch_length=-2)
plot_polygon(poly, ax=ax3, color=GRAY, alpha=0.3, add_points=False)
plot_line(centerline, ax=ax3, color=BLUE, alpha=0.7)

# 4: fancy L shape, min_branch_length=-2, extend=True
# ---------------------------------------------------
ax4.set_title("d) min_branch_length=-2, extend=True")
ax4.set_aspect("equal")

poly = shapely.from_wkt(fancy_t_poly_wkt)
centerline = pygeoops.centerline(poly, extend=True, min_branch_length=-2)
plot_polygon(poly, ax=ax4, color=GRAY, alpha=0.3, add_points=False)
plot_line(centerline, ax=ax4, color=BLUE, alpha=0.7)

plt.show()
