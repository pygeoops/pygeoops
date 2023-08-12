import enum

import shapely


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
    def _missing_(cls, value):
        """
        Expand options in the Geometrytype() constructor.

        Args:
            value (Union[str, int, GeometryType]):
                * string: lookup using case insensitive name
                * int: lookup using value
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
    def empty(self) -> str:
        """Get an empty geometry instance of this type."""
        if self is GeometryType.POINT:
            return shapely.Point()
        elif self is GeometryType.LINESTRING:
            return shapely.LineString()
        elif self is GeometryType.POLYGON:
            return shapely.Polygon()
        elif self is GeometryType.MULTIPOINT:
            return shapely.MultiPoint()
        elif self is GeometryType.MULTILINESTRING:
            return shapely.MultiLineString()
        elif self is GeometryType.MULTIPOLYGON:
            return shapely.MultiPolygon()
        elif self is GeometryType.GEOMETRYCOLLECTION:
            return shapely.GeometryCollection()
        elif self is GeometryType.GEOMETRY:
            return shapely.GeometryCollection()
        else:
            raise ValueError(f"No empty implemented for {self}")

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
            raise ValueError(f"No camelcase name implemented for {self}")

    @property
    def is_multitype(self):
        """Returns if the geometry type is a multi type."""
        return self in (
            GeometryType.MULTIPOINT,
            GeometryType.MULTILINESTRING,
            GeometryType.MULTIPOLYGON,
            GeometryType.GEOMETRYCOLLECTION,
        )

    @property
    def to_multitype(self):
        """Get the corresponding multitype."""
        if self in [
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
        elif self is GeometryType.GEOMETRY:
            return GeometryType.GEOMETRYCOLLECTION
        else:
            raise ValueError(f"No multitype implemented for {self}")

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
        elif self is GeometryType.GEOMETRYCOLLECTION:
            return GeometryType.GEOMETRY
        else:
            raise ValueError(f"No singletype implemented for {self}")

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
            return PrimitiveType.GEOMETRY
        else:
            raise ValueError(f"No primitivetype implemented for {self}")


class PrimitiveType(enum.Enum):
    """
    Enumeration of the different existing primitive types of a geometry.
    """

    GEOMETRY = 0
    POINT = 1
    LINESTRING = 2
    POLYGON = 3

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(PrimitiveType[value.upper()])
        return super()._missing_(value)

    @property
    def dimensions(self) -> int:
        """Get the number of dimensions of the type."""
        if self is PrimitiveType.POINT:
            return 0
        elif self is PrimitiveType.LINESTRING:
            return 1
        elif self is PrimitiveType.POLYGON:
            return 2
        else:
            raise ValueError(f"no dimensions implemented for {self}")

    @property
    def to_multitype(self) -> GeometryType:
        """Get the corresponding multitype."""
        if self is PrimitiveType.POINT:
            return GeometryType.MULTIPOINT
        elif self is PrimitiveType.LINESTRING:
            return GeometryType.MULTILINESTRING
        elif self is PrimitiveType.POLYGON:
            return GeometryType.MULTIPOLYGON
        elif self is PrimitiveType.GEOMETRY:
            return GeometryType.GEOMETRYCOLLECTION
        else:
            raise ValueError(f"No multitype implemented for {self}")

    @property
    def to_singletype(self) -> GeometryType:
        """Get the corresponding multitype."""
        if self is PrimitiveType.POINT:
            return GeometryType.POINT
        elif self is PrimitiveType.LINESTRING:
            return GeometryType.LINESTRING
        elif self is PrimitiveType.POLYGON:
            return GeometryType.POLYGON
        elif self is PrimitiveType.GEOMETRY:
            return GeometryType.GEOMETRY
        else:
            raise ValueError(f"No singletype implemented for {self}")
