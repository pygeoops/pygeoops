from typing import List, Optional, Union
import pyproj

import shapely
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from pygeoops._types import GeometryType, PrimitiveType


def collect(
    geometry_list: List[BaseGeometry],
) -> Optional[BaseGeometry]:
    """
    Collect a list of geometries to one geometry.

    Examples:
      * if the list contains only Polygon's, returns a MultiPolygon.
      * if the list contains different types, returns a GeometryCollection.

    Args:
        geometry_list (List[BaseGeometry]): [description]

    Raises:
        Exception: raises an exception if one of the input geometries is of an
            unknown type.

    Returns:
        BaseGeometry: the result
    """
    # First remove all None geometries in the input list
    geometry_list = [
        geometry
        for geometry in geometry_list
        if geometry is not None and geometry.is_empty is False
    ]

    # If the list is empty or contains only 1 element, it is easy...
    if geometry_list is None or len(geometry_list) == 0:
        return None
    elif len(geometry_list) == 1:
        return geometry_list[0]

    # Loop over all elements in the list, and determine the appropriate geometry
    # type to create
    result_collection_type = GeometryType(geometry_list[0].geom_type).to_multitype
    for geom in geometry_list:
        # If it is the same as the collection_geom_type, continue checking
        if GeometryType(geom.geom_type).to_multitype == result_collection_type:
            continue
        else:
            # If multiple types in the list, result becomes a geometrycollection
            result_collection_type = GeometryType.GEOMETRYCOLLECTION
            break

    # Now we can create the collection
    # Explode the multi-geometries to single ones
    singular_geometry_list = []
    for geom in geometry_list:
        if isinstance(geom, BaseMultipartGeometry):
            singular_geometry_list.extend(geom.geoms)
        else:
            singular_geometry_list.append(geom)

    if result_collection_type == GeometryType.MULTIPOINT:
        return shapely.MultiPoint(singular_geometry_list)
    elif result_collection_type == GeometryType.MULTILINESTRING:
        return shapely.MultiLineString(singular_geometry_list)
    elif result_collection_type == GeometryType.MULTIPOLYGON:
        return shapely.MultiPolygon(singular_geometry_list)
    elif result_collection_type == GeometryType.GEOMETRYCOLLECTION:
        return shapely.GeometryCollection(geometry_list)
    else:
        raise Exception(f"Unsupported geometry type: {result_collection_type}")


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
        raise Exception(f"Invalid/unsupported geometry(type): {geometry}")

    # Nothing found yet, so return None
    return None


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
        raise Exception(f"Unsupported geometrytype: {dest_geometrytype}")
"""


def remove_inner_rings(
    geometry: Union[shapely.Polygon, shapely.MultiPolygon, None],
    min_area_to_keep: float,
    crs: Optional[pyproj.CRS],
) -> Union[shapely.Polygon, shapely.MultiPolygon, None]:
    """
    Remove (small) inner rings from a (multi)polygon.

    Args:
        geometry (Union[shapely.Polygon, shapely.MultiPolygon, None]): polygon
        min_area_to_keep (float, optional): keep the inner rings with at least
            this area in the coordinate units (typically m). If 0.0,
            no inner rings are kept.
        crs (pyproj.CRS, optional): the projection of the geometry. Passing
            None is fine if min_area_to_keep and/or the geometry is in a
            projected crs (not in degrees). Otherwise the/a crs should be
            passed.

    Raises:
        Exception: if the input geometry is no (multi)polygon.

    Returns:
        Union[shapely.Polygon, shapely.MultiPolygon, None]: the resulting
            (multi)polygon.
    """
    # If input geom is None, just return.
    if geometry is None:
        return None

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
        raise Exception(
            f"remove_inner_rings impossible on {geometry.geom_type}: {geometry}"
        )
