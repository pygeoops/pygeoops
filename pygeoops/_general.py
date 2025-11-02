import copy
import math
import warnings

import numpy as np
import pyproj
import shapely
from geopandas import GeoSeries
from numpy.typing import ArrayLike, NDArray
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

import pygeoops
from pygeoops._types import GeometryType, PrimitiveType


def collect(geometries) -> BaseGeometry | None:
    """Collects a list of geometries to one (multi)geometry.

    Elements in the list that are None or empty geometries are dropped.

    Examples:
      * if the list contains only Polygon's, returns a MultiPolygon.
      * if the list contains different types (and Multipolygon != Polygon!), returns a
        GeometryCollection.

    Args:
        geometries (geometry, GeoSeries or arraylike): geometry or arraylike.

    Raises:
        ValueError: raises an exception if one of the input geometries is of an
            unknown type.

    Returns:
        BaseGeometry: the result.
    """
    # If geometry_list is None or no list, just return itself
    if geometries is None:
        return None
    geometries = _extract_0dim_ndarray(geometries)
    if not hasattr(geometries, "__len__"):
        return geometries

    # Only keep geometries in the input list that are not None nor empty
    geometries = [
        geom for geom in geometries if geom is not None and geom.is_empty is False
    ]

    # If the list is empty or contains only 1 element, it is easy...
    if geometries is None or len(geometries) == 0:
        return None
    elif len(geometries) == 1:
        return geometries[0]

    # Loop over all elements in the list, and determine the appropriate geometry
    # type to create
    result_collection_type = None
    for geom in geometries:
        if isinstance(geom, BaseMultipartGeometry):
            # If geom is a multitype, the result needs to be a GeometryCollection,
            # as this is the only type that can contain Multi-types.
            result_collection_type = GeometryType.GEOMETRYCOLLECTION
            break

        geometrytype = GeometryType(geom.geom_type)
        if result_collection_type is None:
            # First element
            result_collection_type = geometrytype.to_multitype
        elif geometrytype.to_multitype == result_collection_type:
            # Same as the previous types encountered, so continue checking
            continue
        else:
            # Another type than current result_collection_type -> GeometryCollection
            result_collection_type = GeometryType.GEOMETRYCOLLECTION
            break

    # Now we can create the collection
    if result_collection_type == GeometryType.MULTIPOINT:
        return shapely.MultiPoint(geometries)
    elif result_collection_type == GeometryType.MULTILINESTRING:
        return shapely.MultiLineString(geometries)
    elif result_collection_type == GeometryType.MULTIPOLYGON:
        # A multipolygon with touching rings is not valid, so try to create it like
        # this, and if it is invalid, create a GeometryCollection
        result = shapely.MultiPolygon(geometries)
        result = result if result.is_valid else shapely.GeometryCollection(geometries)
        return result

    elif result_collection_type == GeometryType.GEOMETRYCOLLECTION:
        return shapely.GeometryCollection(geometries)
    else:
        raise ValueError(f"Unsupported geometry type: {result_collection_type}")


def _extract_0dim_ndarray(geometry):
    # If the geometry is a 0 dimension ndarray, return it as simple geometry
    if isinstance(geometry, np.ndarray) and np.ndim(geometry) == 0:
        return geometry.item()

    return geometry


def collection_extract(
    geometry,
    primitivetype: int | PrimitiveType | ArrayLike | None = None,
) -> BaseGeometry | NDArray[BaseGeometry] | None:
    """Extracts the parts from the input that comply with the type specified.

    Args:
        geometry (geometry, GeoSeries or arraylike): geometry or arraylike.
        primitivetype (Union[int, PrimitiveType] or arraylike): the type of geometries
            to keep in the output. Either one or an arraylike of PrimitiveType or an int
            with one of the following values: 0: all, 1: points, 2: lines, 3: polygons.

    Raises:
        ValueError: if geometry is an unsupported geometry type or (a) primitivetype is
            invalid.

    Returns:
        Union[BaseGeometry, NDArray[BaseGeometry], None]: geometry or array of
            geometries containing only parts of the primitive type specified.
    """
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)

    def to_primitivetype_id(pri_type) -> int:
        if isinstance(pri_type, PrimitiveType):
            pri_type = pri_type.value
        elif isinstance(pri_type, int | np.integer):
            if pri_type not in [0, 1, 2, 3]:
                raise ValueError(f"Invalid value for primitivetype: {pri_type}")
        elif pri_type is None:
            raise ValueError("Invalid value for primitivetype: None")
        else:
            raise ValueError(f"Invalid type for primitivetype: {type(pri_type)}")

        return pri_type

    # Valide + prepare primitivetype param
    if not _is_arraylike(primitivetype):
        # Single primitive type
        primitivetype = to_primitivetype_id(primitivetype)

        # If we need to extract everything, we can just return the input
        if primitivetype == 0:
            return geometry

        # Arraylike geometries, so convert primitivetype to a list of same length
        if _is_arraylike(geometry):
            primitivetype = [primitivetype] * len(geometry)

    else:
        # Arraylike -> convert to list of primitivetype ids
        primitivetype = [to_primitivetype_id(type) for type in primitivetype]  # type: ignore[union-attr]

        if _is_arraylike(geometry):
            # Number of primitive types specified should equal the number of geometries
            if len(primitivetype) != len(geometry):
                raise ValueError(
                    "geometry and primitivetype are arraylike, so len must be equal"
                )
        else:
            # A single geometry: not compatible with the arraylike primitivetype!
            raise ValueError("single geometry passed, but primitivetype is arraylike")

    # Run the collection extraction
    if not _is_arraylike(geometry):
        # Single geometry.
        result = _collection_extract(geometry=geometry, primitivetype_id=primitivetype)  # type: ignore[arg-type]
    else:
        # Arraylike geometries -> run on all of them
        result = np.array(
            [
                _collection_extract(geometry=geom, primitivetype_id=type)
                for geom, type in zip(geometry, primitivetype, strict=True)  # type: ignore[arg-type]
            ]
        )
        # If input is GeoSeries, recover index
        if isinstance(geometry, GeoSeries):
            result = GeoSeries(result, index=geometry.index, crs=geometry.crs)

    # Apply makevalid, because possibly touching polygons were merged to a multipolygon,
    # which isn't valid.
    # Note: keep_collapsed cannot be False, otherwise we can get in a never ending loop
    # because make_valid the uses collection_extract!
    # return pygeoops.make_valid(result, keep_collapsed=True, only_if_invalid=True)
    return result


def _collection_extract(
    geometry: BaseGeometry | None, primitivetype_id: int
) -> BaseGeometry | None:
    if geometry is None:
        return None
    if primitivetype_id == 0:
        return geometry
    if isinstance(geometry, np.ndarray) and np.ndim(geometry) == 0:
        # geometry is a single-element ndarray: this is not supported
        raise ValueError(
            "input geometry is a 1-element ndarray, extract it using geometry.item()"
        )

    if isinstance(geometry, shapely.MultiPoint | shapely.Point):
        if primitivetype_id == 1:
            return geometry
    elif isinstance(geometry, shapely.LineString | shapely.MultiLineString):
        if primitivetype_id == 2:
            return geometry
    elif isinstance(geometry, shapely.MultiPolygon | shapely.Polygon):
        if primitivetype_id == 3:
            return geometry
    elif isinstance(geometry, shapely.GeometryCollection):
        returngeoms = [
            _collection_extract(geom, primitivetype_id=primitivetype_id)
            for geom in geometry.geoms
        ]
        if len(returngeoms) > 0:
            return collect(returngeoms)
    else:
        raise ValueError(f"Invalid/unsupported geometry(type): {geometry}")

    return None


def empty(geometrytype: int | GeometryType | None) -> BaseGeometry | None:
    """Generate an empty geometry of the type specified.

    Args:
        geometrytype (GeometryType or int): geometrytype or geometrytype id of the empty
            geometry to return.

    Returns:
        Optional[BaseGeometry]: empty geometry of the type asked or None.
    """
    if geometrytype is None:
        return None
    if not isinstance(geometrytype, GeometryType):
        geometrytype = GeometryType(geometrytype)

    return geometrytype.empty


def explode(geometry: BaseGeometry | None) -> NDArray[BaseGeometry] | None:
    """Return the parts of the input as an array.

    Args:
        geometry (BaseGeometry, optional): geometry to explode.

    Returns:
        Optional[NDArray[BaseGeometry]]: array with the parts of the input geometry or
            None if the input was None.

    """
    warnings.warn(
        "Deprecated: use shapely.get_parts() instead", DeprecationWarning, stacklevel=2
    )
    if geometry is None:
        return None
    return shapely.get_parts(geometry)


"""
def force_geometrytype(
        geometry: BaseGeometry,
        dest_geometrytype: GeometryType) -> BaseGeometry:
    # Cast to destination geometrytype
    if dest_geometrytype is GeometryType.MULTIPOLYGON:
        gdf.geometry = [shapely.MultiPolygon([feature])
                        if type(feature) == shapely.Polygon
                        else feature for feature in gdf.geometry]
    elif dest_geometrytype is GeometryType.MULTIPOINT:
        gdf.geometry = [shapely.MultiPoint([feature])
                        if type(feature) == shapely.Point
                        else feature for feature in gdf.geometry]
    elif dest_geometrytype is GeometryType.MULTILINESTRING:
        gdf.geometry = [shapely.MultiLineString([feature])
                        if type(feature) == shapely.LineString
                        else feature for feature in gdf.geometry]
    elif dest_geometrytype in [
            GeometryType.POLYGON, GeometryType.POINT, GeometryType.LINESTRING]:
        logger.debug(f"geometrytype is {dest_geometrytype}, so no conversion is done")
    else:
        raise ValueError(f"Unsupported geometrytype: {dest_geometrytype}")
"""


def format_short(geometry: BaseGeometry | None) -> str:
    """Formats a geometry with only the first point included for display.

    Args:
        geometry (BaseGeometry, optional): The geometry to format.

    Returns:
        str: A string representation of the geometry including only the first point.
    """
    if geometry is None:
        return "None"

    if isinstance(geometry, shapely.Point):
        return f"POINT({geometry.x} {geometry.y})"
    elif isinstance(geometry, (shapely.LinearRing | shapely.LineString)):
        first_point = shapely.get_point(geometry, 0)
        return (
            f"{type(geometry).__name__.upper()}({first_point.x} {first_point.y}, ...)"
        )
    elif isinstance(geometry, shapely.Polygon):
        first_point = shapely.get_point(geometry.exterior, 0)
        return f"POLYGON({first_point.x} {first_point.y}, ...)"
    elif isinstance(geometry, shapely.MultiPolygon):
        first_point = shapely.get_point(shapely.get_geometry(geometry, 0).exterior, 0)
        return f"MULTIPOLYGON(({first_point.x} {first_point.y}, ...)"
    elif isinstance(geometry, shapely.MultiPoint):
        if shapely.get_num_geometries(geometry) > 1:
            first_point = shapely.get_geometry(geometry, 0)
            return f"MULTIPOINT({first_point.x} {first_point.y}, ...)"
        else:
            first_point = shapely.get_geometry(geometry, 0)
            return f"MULTIPOINT({first_point.x} {first_point.y})"
    elif isinstance(geometry, shapely.MultiLineString):
        first_point = shapely.get_point(shapely.get_geometry(geometry, 0), 0)
        return f"MULTILINESTRING(({first_point.x} {first_point.y}, ...)"

    # Loop till it isn't a multipart geometry anymore
    result = ""
    multi = False
    while isinstance(geometry, shapely.GeometryCollection):
        if shapely.get_num_geometries(geometry) > 1:
            multi = True
        result += f"{type(geometry).__name__.upper()}("
        geometry = shapely.get_geometry(geometry, 0)

    suffix = ", ...)" if multi else ")"
    result += format_short(geometry)
    if not result.endswith(", ...)"):
        result += suffix

    return result


def get_parts_recursive(geometry: BaseGeometry | None):
    """Recursively get all parts of the input till only single geometries remain.

    Even if there is deep nesting of multipart geometries, all parts are extracted to
    one flat array.

    .. versionadded:: 0.6.0

    Args:
        geometry (BaseGeometry, optional): geometry to get the parts for.

    Returns:
        Optional[NDArray[BaseGeometry]]: array of simple geometries or None if the input
            was None.

    """
    if geometry is None:
        return None
    if not isinstance(geometry, BaseMultipartGeometry):
        return np.array([geometry])

    parts = shapely.get_parts(geometry)
    while True:
        new_parts = []
        multi_found = False
        for part in parts:
            if isinstance(part, BaseMultipartGeometry):
                # Multipart geometry -> get its parts as well
                subparts = shapely.get_parts(part)
                new_parts.append(subparts)
                multi_found = True
            else:
                new_parts.append([part])

        if multi_found:
            # At least one multipart geometry found -> continue
            parts = np.concatenate(new_parts)
        else:
            # No more multipart geometries found -> stop
            break

    return parts


def get_primitivetype_id(geometry) -> int | NDArray[np.number]:
    """Determines for each input geometry which is the primitive type of the geometry.

    Args:
        geometry (geometry, GeoSeries or arraylike): geometry or arraylike.

    Returns:
        Union[int, NDArray[np.number]]: int or array of integers with for each input
            geometry its Primitivetype_id.
    """
    # Prepare input
    geometry = _extract_0dim_ndarray(geometry)

    # If input is arraylike
    if _is_arraylike(geometry):
        # Determine which are geometry collections
        types = shapely.get_type_id(geometry)
        collections_mask = types == 7
        # Determine the "standard" dimensions an add 1 to get primitive type id
        primitivetype_id = shapely.get_dimensions(geometry) + 1

        # Overwrite primitivetype with 0 for geometrycollections
        primitivetype_id[collections_mask] = 0
    elif isinstance(geometry, shapely.GeometryCollection):
        primitivetype_id = 0
    else:
        primitivetype_id = shapely.get_dimensions(geometry) + 1

    return primitivetype_id


def _is_arraylike(a) -> bool:
    return not isinstance(a, str) and hasattr(a, "__len__")


def make_valid(geometry, keep_collapsed: bool = True, only_if_invalid: bool = False):
    """Make the input geometry valid.

    If the input geometry is already valid, it will be returned. If the geometry must be
    split into multiple parts of the same type to be made valid, a multi-part geometry
    will be returned. If the geometry must be split into multiple parts of different
    types to be made valid, a GeometryCollection will be returned if
    `keep_collapsed=True`.

    Args:
        geometry (geometry, GeoSeries or arraylike): geometry or arraylike.
        keep_collapsed (bool, optional): When False, geometry components that collapse
            to a lower dimensionality, for example a one-point linestring, are dropped.
            Defaults to True.
        only_if_invalid (bool, optional): When True, `is_valid` is ran before applying
            `make_valid` only for the geometries that need it. If many input geometries
            are valid this is faster.

    Returns:
        geometry, GeoSeries or array_like: the valid version for each of the input
            geometries.
    """
    # Prepare input
    geometry = _extract_0dim_ndarray(geometry)
    if geometry is None:
        return None

    if only_if_invalid:
        is_valid = shapely.is_valid(geometry)

        # Apply make_valid only on the invalid geometries
        if np.count_nonzero(~is_valid) > 0:
            result = np.array(geometry)
            result[~is_valid] = _make_valid(result[~is_valid], keep_collapsed)
            result = _extract_0dim_ndarray(result)
        # No make_valid needed, but copy because we're supposed to return a copy
        elif not hasattr(geometry, "__len__"):
            result = copy.deepcopy(geometry)
        else:
            result = np.array(geometry)

    else:
        result = _make_valid(geometry, keep_collapsed)

    # If input is GeoSeries, return one with same index
    if isinstance(geometry, GeoSeries):
        return GeoSeries(result, index=geometry.index, crs=geometry.crs)

    return result


def _make_valid(geometry, keep_collapsed: bool = True):
    # Prepare input
    geometry = _extract_0dim_ndarray(geometry)

    result = shapely.make_valid(geometry)
    if not keep_collapsed:
        primitivetype = pygeoops.get_primitivetype_id(geometry)
        result = pygeoops.collection_extract(result, primitivetype=primitivetype)

    return result


def remove_inner_rings(
    geometry: shapely.Polygon | shapely.MultiPolygon | None,
    min_area_to_keep: float,
    crs: str | pyproj.CRS | None,
) -> shapely.Polygon | shapely.MultiPolygon | None:
    """Remove (small) inner rings from a (multi)polygon.

    Args:
        geometry (Union[shapely.Polygon, shapely.MultiPolygon, None]): polygon geometry.
        min_area_to_keep (float): keep the inner rings with at least this area
            in the coordinate units (typically m). If 0.0, no inner rings are kept.
        crs (Union[str, pyproj.CRS]): the projection of the geometry. Passing
            None is fine if min_area_to_keep and/or the geometry is in a
            projected crs (not in degrees). Otherwise the/a crs should be passed.

    Raises:
        Exception: if the input geometry is no (multi)polygon.

    Returns:
        Union[shapely.Polygon, shapely.MultiPolygon, None]: the resulting (multi)polygon
    """
    # If input geom is None, just return.
    if geometry is None:
        return None
    if crs is not None and isinstance(crs, str):
        crs = pyproj.CRS(crs)
    geometry = _extract_0dim_ndarray(geometry)

    # Define function to treat simple polygons
    def remove_inner_rings_polygon(
        geom_poly: shapely.Polygon,
        min_area_to_keep: float | None = None,
        crs: pyproj.CRS | None = None,
    ) -> shapely.Polygon:
        # If all inner rings need to be removed...
        if min_area_to_keep is None or min_area_to_keep == 0.0:
            # If there are no interior rings anyway, just return input
            if len(geom_poly.interiors) == 0:
                return geom_poly
            else:
                # Else create new polygon with only the exterior ring
                return shapely.Polygon(geom_poly.exterior)

        # If only small rings need to be removed... loop over them
        ring_coords_to_keep = []
        small_ring_found = False
        for ring in geom_poly.interiors:
            # Calculate area
            if crs is None:
                ring_area = shapely.Polygon(ring).area
            elif crs.is_projected is True:
                ring_area = shapely.Polygon(ring).area
            else:
                geod = crs.get_geod()
                assert geod is not None
                ring_area, _ = geod.geometry_area_perimeter(ring)

            # If ring area small, skip it, otherwise keep it
            if abs(ring_area) <= min_area_to_keep:
                small_ring_found = True
            else:
                ring_coords_to_keep.append(ring.coords)

        # If no small rings were found, just return input
        if small_ring_found is False:
            return geom_poly
        else:
            assert geom_poly.exterior is not None
            return shapely.Polygon(geom_poly.exterior.coords, ring_coords_to_keep)

    # If the input is a simple Polygon, apply remove on it and return.
    if isinstance(geometry, shapely.Polygon):
        return remove_inner_rings_polygon(geometry, min_area_to_keep, crs=crs)
    elif isinstance(geometry, shapely.MultiPolygon):
        # If the input is a MultiPolygon, apply remove on each Polygon in it.
        polys = []
        for poly in geometry.geoms:
            polys.append(remove_inner_rings_polygon(poly, min_area_to_keep, crs=crs))
        return shapely.MultiPolygon(polys)
    else:
        raise ValueError(
            f"remove_inner_rings impossible on {geometry.geom_type}: {geometry}"
        )


def subdivide(
    geometry: BaseGeometry, num_coords_max: int = 1000
) -> NDArray[BaseGeometry]:
    """Divide the input geometry to smaller parts using rectilinear lines.

    Args:
        geometry (geometry): the geometry to subdivide.
        num_coords_max (int): number of coordinates per subdivision to aim for. In the
            current implementation, num_coords_max will be the average number of
            coordinates the subdividions will consist of. If <=0, no subdivision is
            applied. Defaults to 1000.

    Returns:
        array of geometries: if geometry has < num_coords_max coordinates, the array
            will contain the input geometry. Otherwise it will contain subdivisions.
    """
    geometry = _extract_0dim_ndarray(geometry)
    if num_coords_max <= 0:
        return np.array([geometry])

    shapely.prepare(geometry)
    num_coords = shapely.get_num_coordinates(geometry)
    if num_coords <= num_coords_max:
        return np.array([geometry])
    else:
        grid = pygeoops.create_grid2(
            total_bounds=geometry.bounds,
            nb_squarish_tiles=math.ceil(num_coords / num_coords_max),
        )
        geom_divided = shapely.intersection(geometry, grid)
        input_primitivetype_id = pygeoops.get_primitivetype_id(geometry)
        assert isinstance(input_primitivetype_id, int | np.integer)
        geom_divided = pygeoops.collection_extract(geom_divided, input_primitivetype_id)
        assert geom_divided is not None

        return geom_divided[~shapely.is_empty(geom_divided)]
