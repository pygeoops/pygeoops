import matplotlib.pyplot as plt
import shapely
from shapely import LineString
from shapely.plotting import plot_line, plot_polygon

import pygeoops

from figures import SIZE, BLACK, BLUE, GRAY, YELLOW

# fig = plt.figure(1, figsize=SIZE, dpi=90)
fig, (ax1, ax2) = plt.subplots(1, 2, layout="constrained")

fancy_l_poly_wkt = "POLYGON ((0 0, 0 8, -2 10, 4 10, 2 8, 2 2, 10 2, 10 0, 0 0))"

# 1: fancy L shape, extend=False
# ------------------------------
poly = shapely.from_wkt(fancy_l_poly_wkt)
centerline = pygeoops.centerline(poly, extend=False)

plot_line(centerline, ax=ax1, add_points=False, color=BLUE, alpha=0.7)
plot_polygon(poly, ax=ax1, color=GRAY, alpha=0.3)

ax1.set_title("a) extend=False")
# Set x and y scale to be equal
ax1.set_aspect("equal")

# 2: fancy L shape, extend=True
# -----------------------------
poly = shapely.from_wkt(fancy_l_poly_wkt)
centerline = pygeoops.centerline(poly, extend=True)

plot_line(centerline, ax=ax2, add_points=False, color=BLUE, alpha=0.7)
plot_polygon(poly, ax=ax2, color=GRAY, alpha=0.3)

ax2.set_title("b) extend=True")

# Set x and y scale to be equal
ax2.set_aspect("equal")

# fig.set_layout_engine("compressed")
# fig.tight_layout()
plt.show()
