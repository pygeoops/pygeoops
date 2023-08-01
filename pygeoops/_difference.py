import concurrent.futures
import math
from typing import Union

import numpy as np
from numpy.typing import NDArray
import shapely
from shapely.geometry.base import BaseGeometry

import pygeoops
from pygeoops import _paramvalidation as paramvalidation


def difference_all_tiled(
    geometry: BaseGeometry,
    geometries_to_subtract,
    keep_geom_type: Union[bool, int] = False,
) -> BaseGeometry:
    """
    Subtracts all geometries in geometries_to_subtract from the input geometry.

    For complex geometries, the input geometry will be tiled to increase performance.
    Because of this, the output geometry can contain extra collinear points in its
    boundary.

    Args:
        geometry (geometry): single geometry to substract geometries from.
        geometries_to_subtract (geometry or arraylike): geometries to substract.
        keep_geom_type (Union[bool, int], optional): True to retain only geometries in
            the output of the type/dimension of the input. If int, you specify the
            geometry type/dimension to retain: 0: points, 1: lines, 2: polygons.
            Defaults to False.

    Returns:
        geometry: the geometry with the geometries_to_subtract subtracted from it.
    """
    # Check input params/init stuff
    if geometry is None:
        return None
    elif not isinstance(geometry, BaseGeometry):
        raise ValueError(f"geometry should be a shapely geometry, not {geometry}")
    if geometry.is_empty:
        return geometry
    if hasattr(geometries_to_subtract, "__len__"):
        if not isinstance(geometries_to_subtract, np.ndarray):
            geometries_to_subtract = np.array(geometries_to_subtract)
    else:
        geometries_to_subtract = np.array([geometries_to_subtract])

    # Determine type dimension of input + what the output type should
    output_dimensions = paramvalidation.keep_geom_type2dimension(
        keep_geom_type, geometry
    )

    # Check which geometries_to_subtract intersect the geometry
    shapely.prepare(geometry)
    geoms_to_subtract_idx = np.nonzero(
        shapely.intersects(geometry, geometries_to_subtract)
    )[0]

    # Split the input geometry if it has many points to speedup processing.
    # Max 1000 coordinates seems to work fine based on some testing.
    geom_diff = _split_if_needed(geometry, 1000)

    """
    # Subtract all intersecting ones
    for idx in geoms_to_subtract_idx:
        geom_to_subtract = geometries_to_subtract[idx]
        geom_diff = _difference_intersecting(
            geom_diff, geom_to_subtract, output_dimensions=output_dimensions
        )

        # Drop empty results
        geom_diff = geom_diff[~shapely.is_empty(geom_diff)]
    """

    # Subtract all intersecting ones
    if len(geom_diff) > 10:
        # If input split in at least 10 parts, process them in parallel
        nb_workers = min(len(geom_diff), 4)
        futures = {}
        with concurrent.futures.ThreadPoolExecutor(nb_workers) as pool:
            for idx in range(len(geom_diff)):
                future = pool.submit(
                    difference_all,
                    geom_diff[idx],
                    geometries_to_subtract[geoms_to_subtract_idx],
                    keep_geom_type=output_dimensions,
                )
                futures[future] = idx

            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                geom_diff[futures[future]] = res
    else:
        for idx in range(len(geom_diff)):
            geom_diff[idx] = difference_all(
                geom_diff[idx],
                geometries_to_subtract[geoms_to_subtract_idx],
                keep_geom_type=output_dimensions,
            )

    # Drop empty results
    geom_diff = geom_diff[~shapely.is_empty(geom_diff)]

    # Prepare result and return it
    if len(geom_diff) == 0:
        if isinstance(geometry, shapely.GeometryCollection):
            result = pygeoops.empty(-1)
        else:
            result = pygeoops.empty(shapely.get_dimensions(geometry))
    elif len(geom_diff) == 1:
        result = geom_diff[0]
    else:
        result = shapely.unary_union(geom_diff)

    return result


def difference_all(
    geometry: BaseGeometry,
    geometries_to_subtract,
    keep_geom_type: Union[bool, int] = False,
) -> BaseGeometry:
    """
    Subtracts all geometries in geometries_to_subtract from the input geometry.

    Args:
        geometry (geometry): single geometry to subtract geometries from.
        geometries_to_subtract (geometry or arraylike): geometries to substract.
        keep_geom_type (Union[bool, int], optional): True to retain only geometries in
            the output of the type/dimension of the input. If int, specify the geometry
            type/dimension to retain: -1: all, 0: points, 1: lines, 2: polygons.
            Defaults to False.

    Returns:
        geometry: the geometry with the geometries_to_subtract subtracted from it.
    """
    # Check input params
    if geometry is None:
        return None
    elif not isinstance(geometry, BaseGeometry):
        raise ValueError(f"geometry should be a shapely geometry, not {geometry}")
    if geometry.is_empty:
        return geometry
    if hasattr(geometries_to_subtract, "__len__"):
        if not isinstance(geometries_to_subtract, np.ndarray):
            geometries_to_subtract = np.array(geometries_to_subtract)
    else:
        geometries_to_subtract = np.array([geometries_to_subtract])

    # Determine type dimension of input + what the output type should
    output_dimensions = paramvalidation.keep_geom_type2dimension(
        keep_geom_type, geometry
    )

    # Check which geometries_to_subtract intersect the geometry
    shapely.prepare(geometry)
    geoms_to_subtract_idx = np.nonzero(
        shapely.intersects(geometry, geometries_to_subtract)
    )[0]

    # Subtract all intersecting ones
    geom_diff = geometry
    for idx in geoms_to_subtract_idx:
        geom_to_subtract = geometries_to_subtract[idx]
        if shapely.intersects(geom_diff, geom_to_subtract):
            geom_diff = shapely.difference(geom_diff, geom_to_subtract)

            # Only keep geometries of the asked type/dimension.
            if output_dimensions >= 0:
                geom_diff = pygeoops.collection_extract(geom_diff, output_dimensions)

            shapely.prepare(geom_diff)

            if shapely.is_empty(geom_diff):
                break

    return geom_diff


def _split_if_needed(
    geometry: BaseGeometry, num_coords_max: int
) -> NDArray[BaseGeometry]:
    """
    Split the input geometry to smaller pieces using a grid so the average number of
    points per grid tile < num_coords_max.

    Args:
        geom (geometry): the geometry to split.
        num_coords_max (int): maximum coordinates the input geometry should contain.

    Returns:
        array of geometries: if geometry has < num_coords_max coordinates, the array
            will contain the input geometry. Otherwise it will have more elements.
    """
    shapely.prepare(geometry)
    num_coords = shapely.get_num_coordinates(geometry)
    if num_coords <= num_coords_max:
        return np.array([geometry])
    else:
        grid = pygeoops.create_grid2(
            total_bounds=geometry.bounds,
            nb_squarish_tiles=math.ceil(num_coords / num_coords_max),
        )
        geom_split = shapely.intersection(geometry, grid)
        input_dimension = shapely.get_dimensions(geometry)
        if input_dimension > 0:
            geom_split = pygeoops.collection_extract(geom_split, input_dimension)
        geom_split = geom_split[~shapely.is_empty(geom_split)]
        return geom_split


def _difference_intersecting(
    geometry,
    geometry_to_subtract: BaseGeometry,
    keep_geom_type: int = -1,
) -> Union[BaseGeometry, NDArray[BaseGeometry]]:
    """
    Subtracts one geometry from one or more geometies. An intersects is called before
    applying difference to speedup if this hasn't been done before.

    Args:
        geometry (geometry or arraylike): geometry/geometries to subtract from.
        geometry_to_subtract (geometry): single geometry to subtract.
        keep_geom_type (Union[bool, int], optional): True to retain only geometries in
            the output of the type/dimension of the input. If int, specify the geometry
            type/dimension to retain: -1: all, 0: points, 1: lines, 2: polygons.
            Defaults to False.

    Returns:
        geometry or arraylike: geometry or array of geometries with the
            geometry_to_subtract subtracted from it/them.
    """
    if geometry is None:
        return None
    if geometry_to_subtract is None:
        return geometry
    if not isinstance(geometry_to_subtract, BaseGeometry):
        raise ValueError(
            f"geometry_to_subtract should be geometry, not {geometry_to_subtract}"
        )
    return_array = True
    if hasattr(geometry, "__len__"):
        if not isinstance(geometry, np.ndarray):
            geometry = np.array(geometry)
    else:
        return_array = False
        geometry = np.array([geometry])

    # Check which input geometries intersect with geom_to_subtract
    # Remarks:
    #   - Using a prepared feature: 10 * faster
    #   - Testing for touches is quite slow, so faster not to do this test
    shapely.prepare(geometry)
    idx_to_diff = np.nonzero(shapely.intersects(geometry, geometry_to_subtract))[0]
    if len(idx_to_diff) > 0:
        # Apply difference on the relevant input geometries.
        to_subtract_arr = np.repeat(geometry_to_subtract, len(idx_to_diff))
        subtracted = shapely.difference(geometry[idx_to_diff], to_subtract_arr)

        # Only keep geometries of the specified dimension.
        if keep_geom_type > -1:
            subtracted = pygeoops.collection_extract(subtracted, keep_geom_type)

        # Take copy of geometry so the input parameter isn't changed.
        geometry = geometry.copy()
        for idx_subtracted, idx_to_diff in enumerate(idx_to_diff):
            geometry[idx_to_diff] = subtracted[idx_subtracted]

    if return_array:
        return geometry
    else:
        return geometry[0]
