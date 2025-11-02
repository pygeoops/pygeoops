"""Example of buffering by M values with different cases."""

import matplotlib.pyplot as plt
from figures import BLUE, GRAY, W
from shapely import LineString
from shapely.plotting import plot_line, plot_polygon

import pygeoops

fig, (ax1, ax2, ax3) = plt.subplots(
    nrows=1, ncols=3, figsize=(W, W / 2), dpi=90, layout="constrained"
)

# Positive M values
# -----------------
ax1.set_aspect("equal")
ax1.set_title("Positive M values")

line = LineString([[6, 9, 1], [0, 7, 1.5], [0, 0, 1.5], [5, 0, 3]])
buffer = pygeoops.buffer_by_m(line)
plot_polygon(buffer, ax=ax1, color=BLUE, alpha=0.3)
plot_line(line, ax=ax1, color=GRAY, alpha=0.7)

# Zero M value
# ------------
ax2.set_aspect("equal")
ax2.set_title("Zero M value")

line = LineString([[6, 9, 1], [0, 7, 0], [0, 0, 1.5], [5, 0, 3]])
buffer = pygeoops.buffer_by_m(line)
plot_polygon(buffer, ax=ax2, color=BLUE, alpha=0.3)
plot_line(line, ax=ax2, color=GRAY, alpha=0.7)

# Negative M value
# ----------------
ax3.set_aspect("equal")
ax3.set_title("Negative M value")

line = LineString([[6, 9, 1], [0, 7, -1.5], [0, 0, 1.5], [5, 0, 3]])
buffer = pygeoops.buffer_by_m(line)
plot_polygon(buffer, ax=ax3, color=BLUE, alpha=0.3)
plot_line(line, ax=ax3, color=GRAY, alpha=0.7)

plt.show()
