"""Module containing utilities regarding operations on geoseries."""

import logging
import warnings

import numpy as np
import shapely
import topojson
from geopandas import GeoSeries
from numpy.typing import NDArray
from shapely.geometry.base import BaseGeometry

import pygeoops
from pygeoops import GeometryType, PrimitiveType
from pygeoops._general import _extract_0dim_ndarray

# Get a logger...
logger = logging.getLogger(__name__)


def simplify_topo(
    geometry,
    tolerance: float,
    algorithm: str = "rdp",
    lookahead: int = 8,
    keep_points_on: BaseGeometry | None = None,
) -> BaseGeometry | NDArray[BaseGeometry] | GeoSeries | None:
    """Applies simplify while retaining common boundaries between all input geometries.

    Args:
        geometry (geometry, GeoSeries or arraylike): a geometry, GeoSeries or arraylike.
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
        keep_points_on (Optional[BaseGeometry], optional): points that
            intersect with this geometry won't be removed by the simplification.
            Defaults to None.

    Returns:
        The simplified geometry/geometries. If the input is a GeoSeries the result is
        returned like that, otherwise the result is returned as an ndarray.
    """
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)
    algorithm = algorithm.lower()

    # If input isn't arraylike or if the arraylike only has one element, creating a
    # topology first is useless.
    if not hasattr(geometry, "__len__") or len(geometry) <= 1:
        return pygeoops.simplify(
            geometry=geometry,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            preserve_topology=True,
            keep_points_on=keep_points_on,
        )

    # Create topologies
    # -----------------
    # If the input is no Geoseries or list, convert it to a list as the topojson library
    # seems to like that best.
    geometries = geometry
    if not isinstance(geometry, GeoSeries | list):
        geometries = geometry.tolist()

    with warnings.catch_warnings():
        message = "invalid value encountered in cast.*"
        warnings.filterwarnings(
            action="ignore", category=RuntimeWarning, message=message
        )
        topo = topojson.Topology(data=geometries, prequantize=False)

    # Simplify all arcs/vectors/boundaries of the topologies
    # ------------------------------------------------------
    topolines = shapely.MultiLineString(topo.output["arcs"])

    # If the algorithm is rdp and no keep_points_on, use shapely
    if algorithm == "rdp" and keep_points_on is None:
        topolines_simpl = shapely.MultiLineString(
            shapely.simplify(
                geometry=shapely.get_parts(topolines),
                tolerance=tolerance,
                preserve_topology=True,
            ).tolist()
        )
    else:
        topolines_simpl = pygeoops.simplify(
            geometry=topolines,
            tolerance=tolerance,
            algorithm=algorithm,
            lookahead=lookahead,
            keep_points_on=keep_points_on,
            preserve_topology=True,
        )
    assert topolines_simpl is not None
    assert isinstance(topolines_simpl, BaseGeometry)

    # Copy the results of the simplified lines back to the topology arcs
    if algorithm in ["lang", "lang+"]:
        # For LANG, a simple copy is OK
        assert isinstance(topolines_simpl, shapely.MultiLineString)
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

    # Convert the simplified topologies back to geometries
    # ----------------------------------------------------
    crs = None
    if isinstance(geometry, GeoSeries):
        crs = geometry.crs
    topo_simpl_gdf = topo.to_gdf(crs=crs)
    topo_simpl_gdf.geometry = topo_simpl_gdf.geometry.make_valid()

    # If the input was of a single geometry type, filter the result so it stays that way
    # ----------------------------------------------------------------------------------
    if isinstance(geometry, GeoSeries):
        types_orig = geometry.geom_type.unique()
    else:
        types_orig = np.unique(shapely.get_type_id(geometry))
    try:
        primitive_types_orig = list(
            {GeometryType(type).to_primitivetype.name for type in types_orig}
        )
    except Exception:
        # Geometry or GeometryCollection don't have a primitive type, so exception is
        # thrown. In this case all geometry types are OK, so don't filter the result.
        primitive_types_orig = None

    if primitive_types_orig is not None and len(primitive_types_orig) == 1:
        # Extract only the desired type from simplified output
        topo_simpl_gdf.geometry = pygeoops.collection_extract(
            topo_simpl_gdf.geometry, PrimitiveType(primitive_types_orig[0])
        )

    # Return result in the appropriate type
    # -------------------------------------
    if isinstance(geometry, GeoSeries):
        return topo_simpl_gdf.geometry
    else:
        return topo_simpl_gdf.geometry.array.to_numpy()
