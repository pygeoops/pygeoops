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

_data_dir = Path(__file__).parent.resolve() / "data"


class TestData:
    crs_epsg = 31370
    point = shapely.Point((0, 0))
    multipoint = shapely.MultiPoint([(0, 0), (10, 10), (20, 20)])
    linestring = shapely.LineString([(0, 0), (10, 10), (20, 20)])
    multilinestring = shapely.MultiLineString(
        [linestring.coords, [(100, 100), (110, 110), (120, 120)]]
    )
    polygon_with_island = shapely.Polygon(
        shell=[(0.01, 0), (0.01, 10), (1, 10), (10, 10), (10, 0), (0.01, 0)],
        holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )
    polygon_no_islands = shapely.Polygon(
        shell=[(100.01, 100), (100.01, 110), (110, 110), (110, 100), (100.01, 100)]
    )
    polygon_with_island2 = shapely.Polygon(
        shell=[(20, 20), (20, 30), (21, 30), (30, 30), (30, 20), (20, 20)],
        holes=[[(22, 22), (22, 28), (28, 28), (28, 22), (22, 22)]],
    )
    multipolygon = shapely.MultiPolygon([polygon_no_islands, polygon_with_island2])
    geometrycollection = shapely.GeometryCollection(
        [
            point,
            multipoint,
            linestring,
            multilinestring,
            polygon_with_island,
            multipolygon,
        ]
    )
    polygon_small_island = shapely.Polygon(
        shell=[(40, 40), (40, 50), (41, 50), (50, 50), (50, 40), (40, 40)],
        holes=[[(42, 42), (42, 43), (43, 43), (43, 42), (42, 42)]],
    )


def get_testfile(testfile: str) -> Path:
    # Prepare filepath
    testfile_path = _data_dir / f"{testfile}.gpkg"
    if testfile_path.exists is False:
        raise ValueError(f"Invalid testfile type: {testfile}")

    return testfile_path


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

    colors = mcolors.TABLEAU_COLORS
    for geom_idx, geom in enumerate(geoms):
        if geom.is_empty:
            continue

        color = colors[list(colors.keys())[geom_idx % len(colors)]]
        if isinstance(geom, (shapely.MultiPolygon, shapely.Polygon)):
            shapely.plotting.plot_polygon(geom, ax=figure.axes[0], color=color)
        elif isinstance(geom, (shapely.LineString, shapely.MultiLineString)):
            shapely.plotting.plot_line(geom, ax=figure.axes[0], color=color)
        elif isinstance(geom, (shapely.MultiPoint, shapely.Point)):
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
