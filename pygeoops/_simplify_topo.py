# -*- coding: utf-8 -*-
"""
Module containing utilities regarding operations on geoseries.
"""

import logging
from typing import Optional, Union

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry
from shapely import geometry as sh_geom
import topojson

import pygeoops
from pygeoops import GeometryType, PrimitiveType

#####################################################################
# First define/init some general variables/constants
#####################################################################

# Get a logger...
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

#####################################################################
# GeoDataFrame helpers
#####################################################################


def simplify_topo(
    geometry: Union[BaseGeometry, np.ndarray, list, gpd.GeoSeries, None],
    tolerance: float,
    algorithm: str = "rdp",
    lookahead: int = 8,
    keep_points_on: Optional[sh_geom.base.BaseGeometry] = None,
) -> Union[BaseGeometry, np.ndarray, list, gpd.GeoSeries, None]:
    """
    Applies simplify while retaining common boundaries between all input geometries.

    Args:
        geometry (geometry or arraylike): the geometry or arraylike of geometries to
            simplify.
        tolerance (float): tolerance to use for simplify:
            * "rdp": distance to use as tolerance
            * "lang": distance to use as tolerance
            * "vw": area to use as tolerance
        algorithm (str, optional): algorithm to use. Defaults to "rdp".
            * "rdp": Ramer Douglas Peuker
            * "lang": Lang
            * "vw": Visvalingal Whyatt
        lookahead (int, optional): lookahead value for algorithms that use this.
            Defaults to 8.
        keep_points_on (Optional[sh_geom.base.BaseGeometry], optional): points that
            intersect with this geometry won't be removed by the simplification.
            Defaults to None.

    Returns:
        Union[BaseGeometry, np.ndarray, list, GeoSeries, None]: the simplified geometry.
    """
    if geometry is None:
        return None

    # If input isn't arraylike or if the arraylike only has one element, just apply
    # simplify as creating a topology first is useless.
    if not hasattr(geometry, "__len__") or len(geometry) <= 1:
        return pygeoops.simplify(
            geometry=geometry,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            preserve_topology=True,
            keep_points_on=keep_points_on,
        )

    topo = topojson.Topology(geometry, prequantize=False)
    topolines = sh_geom.MultiLineString(topo.output["arcs"])
    topolines_simpl = pygeoops.simplify(
        geometry=topolines,
        tolerance=tolerance,
        algorithm=algorithm,
        lookahead=lookahead,
        keep_points_on=keep_points_on,
        preserve_topology=True,
    )
    assert topolines_simpl is not None

    # Copy the results of the simplified lines
    if algorithm == "lang":
        # For LANG, a simple copy is OK
        assert isinstance(topolines_simpl, sh_geom.MultiLineString)
        topo.output["arcs"] = [list(geom.coords) for geom in topolines_simpl.geoms]
    else:
        # For rdp, only overwrite the lines that have a valid result
        for index in range(len(topo.output["arcs"])):
            # If the result of the simplify is a point, keep original
            topoline_simpl = topolines_simpl.geoms[index].coords
            if len(topoline_simpl) < 2:
                continue
            elif (
                list(topoline_simpl[0]) != topo.output["arcs"][index][0]
                or list(topoline_simpl[-1]) != topo.output["arcs"][index][-1]
            ):
                # Start or end point of the simplified version is not the same anymore
                continue
            else:
                topo.output["arcs"][index] = list(topoline_simpl)

    crs = None
    if isinstance(geometry, gpd.GeoSeries):
        crs = geometry.crs
    topo_simpl_gdf = topo.to_gdf(crs=crs)
    topo_simpl_gdf.geometry = topo_simpl_gdf.geometry.make_valid()

    # If the input was of a single geometry type, filter the result so it stays that way
    if isinstance(geometry, gpd.GeoSeries):
        types_orig = geometry.geom_type.unique()
    else:
        types_orig = np.unique(shapely.get_type_id(geometry))
    try:
        primitive_types_orig = list(
            {GeometryType(type).to_primitivetype.name for type in types_orig}
        )
    except Exception:
        # Geometry or GeometryCollection don't have a primitive type, so exception. In
        # this case all types of gometries are possible, so no need to filter the result
        primitive_types_orig = None

    if primitive_types_orig is not None and len(primitive_types_orig) == 1:
        # If output contains different types, extract only the desired type.
        geometry_types_simpl = topo_simpl_gdf.geometry.geom_type.unique()
        primitive_types_simpl = list(
            {GeometryType(type).to_primitivetype.name for type in geometry_types_simpl}
        )
        if (
            len(primitive_types_simpl) > 1
            or primitive_types_orig[0] != primitive_types_simpl[0]
        ):
            topo_simpl_gdf.geometry = pygeoops.collection_extract(
                topo_simpl_gdf.geometry.array,
                PrimitiveType(primitive_types_orig[0]),
            )

    # Ready
    if isinstance(geometry, gpd.GeoSeries):
        return topo_simpl_gdf.geometry
    else:
        return topo_simpl_gdf.geometry.array.data


def geometry_collection_extract(
    geoseries: gpd.GeoSeries, primitivetype: PrimitiveType
) -> gpd.GeoSeries:
    """
    # Apply the collection_extract
    return pd.GeoSeries(
        [geometry_util.collection_extract(geom, primitivetype) for geom in geoseries])
    """
    # Apply the collection_extract
    geoseries_copy = geoseries.copy()
    for index, geom in geoseries_copy.items():
        geoseries_copy[index] = pygeoops.collection_extract(geom, primitivetype)
    assert isinstance(geoseries_copy, gpd.GeoSeries)
    return geoseries_copy
