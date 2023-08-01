from typing import Union
import numpy as np

import shapely


def keep_geom_type2dimension(keep_geom_type: Union[bool, int], geometry) -> int:
    """
    Checks and interpretes a keep_geom_type parameter and returns the appropriate
    geometry type dimension.

    Args:
        keep_geom_type (Union[bool, int]): value to check and interprete
        geometry (geometry): the geometry

    Raises:
        ValueError: Invalid value for keep_geom_type.

    Returns:
        int: the geometry dimension to keep: -1: all, 0: points, 1: lines, 2: polygons.
    """
    # Determine type dimension of input + what the output type should
    if isinstance(keep_geom_type, bool):
        # If input is a bool, determine dimension
        if not keep_geom_type:
            return -1
        elif isinstance(geometry, shapely.GeometryCollection):
            # For a geometry collection input, keep everything
            return -1
        else:
            # Keep the dimension of the input
            return shapely.get_dimensions(geometry)
    elif isinstance(keep_geom_type, (int, np.integer)):
        # If it is already an int, just validate the value is valid
        if keep_geom_type not in (-1, 0, 1, 2):
            raise ValueError(f"Invalid value for keep_geom_type: {keep_geom_type}")
        return keep_geom_type
    else:
        raise ValueError(f"Invalid type for keep_geom_type: {type(keep_geom_type)}")
