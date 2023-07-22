import enum
from typing import Union


class GeometryType(enum.Enum):
    """
    Enumeration of the different geometry types.
    """

    MISSING = -1
    GEOMETRY = 0
    POINT = 1
    LINESTRING = 2
    POLYGON = 3
    MULTIPOINT = 4
    MULTILINESTRING = 5
    MULTIPOLYGON = 6
    GEOMETRYCOLLECTION = 7

    @classmethod
    def _missing_(cls, value: Union[str, int]):
        """
        Expand options in the Geometrytype() constructor.

        Args:
            value (Union[str, int, GeometryType]):
                * string: lookup using case insensitive name
                * GeometryType: create the same GeometryType as the one passed in

        Returns:
            [GeometryType]: the corresponding GeometryType.
        """
        if isinstance(value, str):
            # If a string is passed in, try lookup based on case insensitive enum name
            return cls(GeometryType[value.upper()])
        # Default behaviour (= lookup based on value)
        return super()._missing_(value)

    @property
    def name_camelcase(self) -> str:
        """Get the name in camel case."""
        if self is GeometryType.POINT:
            return "Point"
        elif self is GeometryType.LINESTRING:
            return "LineString"
        elif self is GeometryType.POLYGON:
            return "Polygon"
        elif self is GeometryType.MULTIPOINT:
            return "MultiPoint"
        elif self is GeometryType.MULTILINESTRING:
            return "MultiLineString"
        elif self is GeometryType.MULTIPOLYGON:
            return "MultiPolygon"
        elif self is GeometryType.GEOMETRYCOLLECTION:
            return "GeometryCollection"
        elif self is GeometryType.GEOMETRY:
            return "Geometry"
        else:
            raise ValueError(f"No camelcase name implemented for: {self}")

    @property
    def is_multitype(self):
        """Returns if the geometry type is a multi type."""
        return self in (
            GeometryType.GEOMETRY,
            GeometryType.MULTIPOINT,
            GeometryType.MULTILINESTRING,
            GeometryType.MULTIPOLYGON,
            GeometryType.GEOMETRYCOLLECTION,
        )

    @property
    def to_multitype(self):
        """Get the corresponding multitype."""
        if self in [
            GeometryType.GEOMETRY,
            GeometryType.MULTIPOINT,
            GeometryType.MULTILINESTRING,
            GeometryType.MULTIPOLYGON,
            GeometryType.GEOMETRYCOLLECTION,
        ]:
            return self
        elif self is GeometryType.POINT:
            return GeometryType.MULTIPOINT
        elif self is GeometryType.LINESTRING:
            return GeometryType.MULTILINESTRING
        elif self is GeometryType.POLYGON:
            return GeometryType.MULTIPOLYGON
        else:
            raise ValueError(f"No multitype implemented for: {self}")

    @property
    def to_singletype(self):
        """Get the corresponding multitype."""
        if self in [
            GeometryType.GEOMETRY,
            GeometryType.POINT,
            GeometryType.LINESTRING,
            GeometryType.POLYGON,
        ]:
            return self
        elif self is GeometryType.MULTIPOINT:
            return GeometryType.POINT
        elif self is GeometryType.MULTILINESTRING:
            return GeometryType.LINESTRING
        elif self is GeometryType.MULTIPOLYGON:
            return GeometryType.POLYGON
        elif GeometryType.GEOMETRYCOLLECTION:
            return GeometryType.GEOMETRY
        else:
            raise ValueError(f"No multitype implemented for: {self}")

    @property
    def to_primitivetype(self):
        """Get the corresponding primitive type."""
        if self in [GeometryType.POINT, GeometryType.MULTIPOINT]:
            return PrimitiveType.POINT
        elif self in [GeometryType.LINESTRING, GeometryType.MULTILINESTRING]:
            return PrimitiveType.LINESTRING
        elif self in [GeometryType.POLYGON, GeometryType.MULTIPOLYGON]:
            return PrimitiveType.POLYGON
        elif self in [GeometryType.GEOMETRY, GeometryType.GEOMETRYCOLLECTION]:
            raise ValueError(f"{self} doesn't have a primitive type")
        else:
            raise ValueError(f"No primitive type implemented for {self}")


class PrimitiveType(enum.Enum):
    """
    Enumeration of the different existing primitive types of a geometry.
    """

    POINT = 1
    LINESTRING = 2
    POLYGON = 3

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(PrimitiveType[value.upper()])
        return super()._missing_(value)

    @property
    def to_multitype(self) -> GeometryType:
        """Get the corresponding multitype."""
        if self is PrimitiveType.POINT:
            return GeometryType.MULTIPOINT
        elif self is PrimitiveType.LINESTRING:
            return GeometryType.MULTILINESTRING
        elif self is PrimitiveType.POLYGON:
            return GeometryType.MULTIPOLYGON
        else:
            raise ValueError(f"no multitype implemented for: {self}")

    @property
    def to_singletype(self) -> GeometryType:
        """Get the corresponding multitype."""
        if self is PrimitiveType.POINT:
            return GeometryType.POINT
        elif self is PrimitiveType.LINESTRING:
            return GeometryType.LINESTRING
        elif self is PrimitiveType.POLYGON:
            return GeometryType.POLYGON
        else:
            raise ValueError(f"no singletype implemented for: {self}")
