import matplotlib.pyplot as plt
import shapely
from shapely import LineString
from shapely.plotting import plot_line, plot_polygon

import pygeoops

from figures import SIZE, BLACK, BLUE, GRAY, YELLOW, set_limits

fig = plt.figure(1, figsize=SIZE, dpi=90)

fancy_l_poly_wkt = "POLYGON ((0 0, 0 8, -2 10, 4 10, 2 8, 2 2, 10 2, 10 0, 0 0))"

# 1: fancy L shape, extend=False
ax = fig.add_subplot(121)
poly = shapely.from_wkt(fancy_l_poly_wkt)
centerline = pygeoops.centerline(poly, extend=False)

plot_line(centerline, ax=ax, add_points=False, color=BLUE, alpha=0.7)
plot_polygon(poly, ax=ax, color=GRAY, alpha=0.3)

ax.set_title("a) extend=False")

# set_limits(ax, -1, 4, -1, 3)

# 2: fancy L shape, extend=True
ax = fig.add_subplot(122)

poly = shapely.from_wkt(fancy_l_poly_wkt)
centerline = pygeoops.centerline(poly, extend=True)

plot_line(centerline, ax=ax, add_points=False, color=BLUE, alpha=0.7)
plot_polygon(poly, ax=ax, color=GRAY, alpha=0.3)

ax.set_title("b) extend=True")

set_limits(ax, -2, 3, -1, 3)

plt.show()
