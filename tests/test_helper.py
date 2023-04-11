# -*- coding: utf-8 -*-
"""
Helper functions for all tests.
"""

import os
from pathlib import Path
import re
from typing import List, Optional

from matplotlib import figure as mpl_figure
import matplotlib.colors as mcolors
import shapely
import shapely.affinity
import shapely.plotting
from shapely.geometry.base import BaseGeometry


def plot(
    geoms: List[BaseGeometry],
    output_path: Path,
    title: Optional[str] = None,
    clean_name: bool = True,
):
    # If we are running on CI server, don't plot
    if "GITHUB_ACTIONS" in os.environ:
        return

    figure = mpl_figure.Figure()
    figure.subplots(1, 1)
    if title is not None:
        figure.suptitle(title)

    colors = mcolors.TABLEAU_COLORS  # type: ignore
    for geom_idx, geom in enumerate(geoms):
        if geom.is_empty:
            continue

        color = colors[list(colors.keys())[geom_idx % len(colors)]]
        if isinstance(geom, shapely.Polygon) or isinstance(geom, shapely.MultiPolygon):
            shapely.plotting.plot_polygon(geom, ax=figure.axes[0], color=color)
        elif isinstance(geom, shapely.LineString) or isinstance(
            geom, shapely.MultiLineString
        ):
            shapely.plotting.plot_line(geom, ax=figure.axes[0], color=color)
        elif isinstance(geom, shapely.Point) or isinstance(geom, shapely.MultiPoint):
            shapely.plotting.plot_points(geom, ax=figure.axes[0], color=color)
        else:
            raise ValueError(f"invalid geom to plot: {geom}")

    if clean_name:
        # Replace all possibly invalid characters by "_"
        output_path = output_path.with_name(re.sub(r"[^\w_. -]", "_", output_path.name))

    figure.savefig(str(output_path), dpi=72)


def translate_to_origin(wkt: str) -> str:
    geom = shapely.from_wkt(wkt)
    bounds = shapely.bounds(geom)
    translated = shapely.affinity.translate(geom, xoff=-bounds[0], yoff=-bounds[1])
    return translated.wkt
