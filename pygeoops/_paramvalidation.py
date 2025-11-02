import numpy as np
from shapely.geometry.base import BaseGeometry

import pygeoops


def keep_geom_type2primitivetype_id(
    keep_geom_type: bool | int, geometry: BaseGeometry
) -> int:
    """Interprete a keep_geom_type parameter and return the appropriate primitivetype.

    Args:
        keep_geom_type (Union[bool, int]): value to check and interprete
        geometry (geometry): the geometry

    Raises:
        ValueError: Invalid value for keep_geom_type.

    Returns:
        int: the primitivetype id to keep: 0: all, 1: points, 2: lines, 3: polygons.
    """
    # Determine primitivetype of input + what the output type should be
    if isinstance(keep_geom_type, bool):
        # If input is a bool with False value, keep everything
        if not keep_geom_type:
            return 0

        primitivetype_id = pygeoops.get_primitivetype_id(geometry)
        assert isinstance(primitivetype_id, int | np.integer)
        return int(primitivetype_id)
    elif isinstance(keep_geom_type, int | np.integer):
        # If it is already an int, just validate the value is valid
        if keep_geom_type not in (0, 1, 2, 3):
            raise ValueError(f"Invalid value for keep_geom_type: {keep_geom_type}")
        return int(keep_geom_type)
    else:
        raise ValueError(f"Invalid type for keep_geom_type: {type(keep_geom_type)}")
