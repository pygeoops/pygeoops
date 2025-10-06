import concurrent.futures
import warnings

import numpy as np
from numpy.typing import NDArray
import shapely
from shapely.geometry.base import BaseGeometry

import pygeoops
from pygeoops import _paramvalidation as valid
from pygeoops._general import _extract_0dim_ndarray


def difference_all_tiled(
    geometry: BaseGeometry,
    geometries_to_subtract,
    keep_geom_type: bool | int = False,
    subdivide_coords: int = 1000,
) -> BaseGeometry:
    """
    Subtracts all geometries in geometries_to_subtract from the input geometry.

    If the input geometry has many points, it can be subdivided in smaller parts
    to potentially speed up processing as controlled by parameter `subdivide_coords`.
    This will result in extra collinear points being added to the boundaries of the
    output.

    Notes:
      - the geometries_to_subtract won't be subdivided, so if they can contain complex
        geometries as well you can use `subdivide` on them first.
      - if geometries_to_subtract is None, the input geometry is returned.
      - best performance will be obtained if only geometries_to_subtract are passed in
        that intersect the input geometry.

    Args:
        geometry (geometry): single geometry to substract geometries from.
        geometries_to_subtract (geometry or arraylike): geometries to substract.
        keep_geom_type (Union[bool, int], optional): True to retain only geometries in
            the output of the primitivetype of the input. If int, you specify the
            primitive type to retain: 0: all, 1: points, 2: lines, 3: polygons.
            Defaults to False.
        subdivide_coords (int): if > 0, the input geometry will be
            subdivided to parts with about this number of points to potentially speedup
            processing. Subdividing can result in extra collinear points being added to
            the boundaries of the output. If <= 0, no subdividing is applied.
            Defaults to 1000.

    Returns:
        geometry: the geometry with the geometries_to_subtract subtracted from it.
    """
    # Check input params/init stuff
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)
    if not isinstance(geometry, BaseGeometry):
        raise ValueError(f"geometry should be a shapely geometry, not {geometry}")
    if geometry.is_empty or geometries_to_subtract is None:
        return geometry

    # Determine type dimension of input + what the output type should
    output_primitivetype_id = valid.keep_geom_type2primitivetype_id(
        keep_geom_type, geometry
    )

    # Prepare geometries_to_subtract for efficient subtracting by exploding them
    if not hasattr(geometries_to_subtract, "__len__"):
        geometries_to_subtract = [geometries_to_subtract]
    geometries_to_subtract = shapely.get_parts(geometries_to_subtract)

    # Split the input geometry if it has many points to speedup processing.
    # Max 1000 coordinates seems to work fine based on some testing.
    geom_diff = pygeoops.subdivide(geometry, subdivide_coords)

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
                    geometries_to_subtract,
                    keep_geom_type=output_primitivetype_id,
                    check_intersects=True,
                )
                futures[future] = idx

            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                geom_diff[futures[future]] = res
    else:
        for idx in range(len(geom_diff)):
            geom_diff[idx] = difference_all(
                geom_diff[idx],
                geometries_to_subtract,
                keep_geom_type=output_primitivetype_id,
                check_intersects=True,
            )

    # Drop empty results
    geom_diff = geom_diff[~shapely.is_empty(geom_diff)]

    # Prepare result and return it
    if len(geom_diff) == 0:
        result = pygeoops.empty(shapely.get_type_id(geometry))
    elif len(geom_diff) == 1:
        result = geom_diff[0]
    else:
        result = shapely.unary_union(geom_diff)

    return result


def difference_all(
    geometry: BaseGeometry,
    geometries_to_subtract,
    keep_geom_type: bool | int = False,
    check_intersects: bool = False,
) -> BaseGeometry:
    """
    Subtracts all geometries in geometries_to_subtract from the input geometry.

    Args:
        geometry (geometry): single geometry to subtract geometries from.
        geometries_to_subtract (geometry or arraylike): geometries to substract.
        keep_geom_type (Union[bool, int], optional): True to retain only geometries in
            the output of the primitivetype of the input. If int, specify the geometry
            primitive type to retain: 0: all, 1: points, 2: lines, 3: polygons.
            Defaults to False.
        check_intersects (bool, optional): True to first check if the
            geometries_to_subtract intersect geometry. This will be faster if some
            geometries_to_subtract don't intersect. Defaults to False.

    Returns:
        geometry: the geometry with the geometries_to_subtract subtracted from it.
    """
    # Check input params
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)
    if not isinstance(geometry, BaseGeometry):
        raise ValueError(f"geometry should be a shapely geometry, not {geometry}")
    if geometry.is_empty:
        return geometry
    if hasattr(geometries_to_subtract, "__len__"):
        if not isinstance(geometries_to_subtract, np.ndarray):
            geometries_to_subtract = np.array(geometries_to_subtract)
    else:
        geometries_to_subtract = np.array([geometries_to_subtract])

    # Determine type dimension of input + what the output type should
    output_primitivetype_id = valid.keep_geom_type2primitivetype_id(
        keep_geom_type, geometry
    )

    # Check which geometries_to_subtract intersect the geometry
    if check_intersects:
        shapely.prepare(geometry)
        geoms_to_subtract_idx = np.nonzero(
            shapely.intersects(geometry, geometries_to_subtract)
        )[0]

        if len(geoms_to_subtract_idx) == 0:
            return geometry
        geometries_to_subtract = geometries_to_subtract[geoms_to_subtract_idx]

    # Apply difference with unioned geometries_to_subtract.
    # This is significantly faster than looping through all to difference them.
    geom_to_subtract = shapely.union_all(geometries_to_subtract)

    # Set handler for warnings, so the geometries involved are are logged as well.
    def err_handler(type, flag):
        warnings.warn(
            f"warning in difference of geom at {shapely.get_coordinates(geometry)[0]}"
            f" with geom at {shapely.get_coordinates(geom_to_subtract)[0]}, "
            f"type: {type}, flag: {flag}",
            stacklevel=1,
        )

    with np.errstate(all="call", call=err_handler):
        geom_diff = shapely.difference(geometry, geom_to_subtract)

    # Only keep geometries of the asked primitivetype.
    geom_diff = pygeoops.collection_extract(geom_diff, output_primitivetype_id)

    return geom_diff


def _difference_intersecting(
    geometry,
    geometry_to_subtract: BaseGeometry,
    primitivetype_id: int = 0,
) -> BaseGeometry | NDArray[BaseGeometry]:
    """
    Subtracts one geometry from one or more geometies.

    An intersects is called before applying difference to speedup if this hasn't been
    done before.

    Args:
        geometry (geometry or arraylike): geometry/geometries to subtract from.
        geometry_to_subtract (geometry): single geometry to subtract.
        primitivetype_id (int, optional): specify the primitivetype_id to retain:
            0: all, 1: points, 2: lines, 3: polygons. Defaults to 0.

    Returns:
        geometry or arraylike: geometry or array of geometries with the
            geometry_to_subtract subtracted from it/them.
    """
    if geometry is None:
        return None
    geometry = _extract_0dim_ndarray(geometry)
    if geometry_to_subtract is None:
        return geometry
    geometry_to_subtract = _extract_0dim_ndarray(geometry_to_subtract)
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

        # Only keep geometries of the specified primitivetype.
        subtracted = pygeoops.collection_extract(subtracted, primitivetype_id)
        assert subtracted is not None

        # Take copy of geometry so the input parameter isn't changed.
        geometry = geometry.copy()
        for idx_subtracted, idx_to_diff in enumerate(idx_to_diff):
            geometry[idx_to_diff] = subtracted[idx_subtracted]

    if return_array:
        return geometry
    else:
        return geometry[0]
