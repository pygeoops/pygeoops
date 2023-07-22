from typing import List, Optional, Union

import pyproj
import shapely
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from pygeoops._types import GeometryType, PrimitiveType


def collect(
    geometries: Union[BaseGeometry, List[BaseGeometry], None],
) -> Optional[BaseGeometry]:
    """
    Collects a list of geometries to one geometry.

    Elements in the list that are None or empty geometries are dropped.

    Examples:
      * if the list contains only Polygon's, returns a MultiPolygon.
      * if the list contains different types (and Multipolygon != Polygon!), returns a
        GeometryCollection.

    Args:
        geometries (List[BaseGeometry]): arraylike list of geometries to collect to one
            geometry.

    Raises:
        ValueError: raises an exception if one of the input geometries is of an
            unknown type.

    Returns:
        BaseGeometry: the result
    """
    # If geometry_list is None or no list, just return itself
    if geometries is None:
        return None
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
            # If geom is a multitype, the result needs to be a GeometryCollection, as
            # this is the only type that can contain Multi-types
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
            # Another type than current result_collection_type, so GeometryCollection
            result_collection_type = GeometryType.GEOMETRYCOLLECTION
            break

    # Now we can create the collection
    if result_collection_type == GeometryType.MULTIPOINT:
        return shapely.MultiPoint(geometries)
    elif result_collection_type == GeometryType.MULTILINESTRING:
        return shapely.MultiLineString(geometries)
    elif result_collection_type == GeometryType.MULTIPOLYGON:
        return shapely.MultiPolygon(geometries)
    elif result_collection_type == GeometryType.GEOMETRYCOLLECTION:
        return shapely.GeometryCollection(geometries)
    else:
        raise ValueError(f"Unsupported geometry type: {result_collection_type}")


def collection_extract(
    geometry: Optional[BaseGeometry], primitivetype: PrimitiveType
) -> Optional[BaseGeometry]:
    """
    Extracts the geometries from the input geom that comply with the
    primitive_type specified and returns them as (Multi)geometry.

    Args:
        geometry (BaseGeometry): geometry to extract the polygons
            from.
        primitivetype (GeometryPrimitiveTypes): the primitive type to extract
            from the input geom.

    Raises:
        Exception: if in_geom is an unsupported geometry type or the primitive
            type is invalid.

    Returns:
        BaseGeometry: List of primitive geometries, only
            containing the primitive type specified.
    """
    # Extract the polygons from the multipolygon, but store them as multipolygons anyway
    if geometry is None:
        return None
    elif isinstance(geometry, (shapely.MultiPoint, shapely.Point)):
        if primitivetype == PrimitiveType.POINT:
            return geometry
    elif isinstance(geometry, (shapely.LineString, shapely.MultiLineString)):
        if primitivetype == PrimitiveType.LINESTRING:
            return geometry
    elif isinstance(geometry, (shapely.MultiPolygon, shapely.Polygon)):
        if primitivetype == PrimitiveType.POLYGON:
            return geometry
    elif isinstance(geometry, shapely.GeometryCollection):
        returngeoms = [
            collection_extract(geometry, primitivetype=primitivetype)
            for geometry in shapely.GeometryCollection(geometry).geoms
        ]
        if len(returngeoms) > 0:
            return collect(returngeoms)
    else:
        raise ValueError(f"Invalid/unsupported geometry(type): {geometry}")

    # Nothing found yet, so return None
    return None


def explode(geometry: Optional[BaseGeometry]) -> Optional[List[BaseGeometry]]:
    """
    Dump all (multi)geometries in the input to one list of single geometries.

    Args:
        geometry (BaseGeometry, optional): geometry to explode.

    Returns:
        Optional[List[BaseGeometry]]: a list of simple geometries or None if the input
            was None.

    """
    if geometry is None:
        return None
    elif isinstance(geometry, BaseMultipartGeometry):
        return list(geometry.geoms)
    else:
        return [geometry]


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


def remove_inner_rings(
    geometry: Union[shapely.Polygon, shapely.MultiPolygon, None],
    min_area_to_keep: float,
    crs: Union[str, pyproj.CRS, None],
) -> Union[shapely.Polygon, shapely.MultiPolygon, None]:
    """
    Remove (small) inner rings from a (multi)polygon.

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

    # Define function to treat simple polygons
    def remove_inner_rings_polygon(
        geom_poly: shapely.Polygon,
        min_area_to_keep: Optional[float] = None,
        crs: Optional[pyproj.CRS] = None,
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
                ring_area, ring_perimeter = geod.geometry_area_perimeter(ring)

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
