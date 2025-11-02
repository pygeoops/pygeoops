import enum
import math

import shapely


class GeometryType(enum.Enum):
    """Enumeration of the different geometry types."""

    MISSING = -1
    GEOMETRY = 0
    POINT = 1
    LINESTRING = 2
    POLYGON = 3
    MULTIPOINT = 4
    MULTILINESTRING = 5
    MULTIPOLYGON = 6
    GEOMETRYCOLLECTION = 7
    POLYHEDRALSURFACE = 15
    TIN = 16
    TRIANGLE = 17
    POINTZ = 1001
    LINESTRINGZ = 1002
    POLYGONZ = 1003
    TRIANGLEZ = 1017
    MULTIPOINTZ = 1004
    MULTILINESTRINGZ = 1005
    MULTIPOLYGONZ = 1006
    GEOMETRYCOLLECTIONZ = 1007
    POLYHEDRALSURFACEZ = 1015
    TINZ = 1016
    POINTM = 2001
    LINESTRINGM = 2002
    POLYGONM = 2003
    TRIANGLEM = 2017
    MULTIPOINTM = 2004
    MULTILINESTRINGM = 2005
    MULTIPOLYGONM = 2006
    GEOMETRYCOLLECTIONM = 2007
    POLYHEDRALSURFACEM = 2015
    TINM = 2016
    POINTZM = 3001
    LINESTRINGZM = 3002
    POLYGONZM = 3003
    TRIANGLEZM = 3017
    MULTIPOINTZM = 3004
    MULTILINESTRINGZM = 3005
    MULTIPOLYGONZM = 3006
    GEOMETRYCOLLECTIONZM = 3007
    POLYHEDRALSURFACEZM = 3015
    TINZM = 3016

    @classmethod
    def _missing_(cls, value):
        """Expand options in the Geometrytype() constructor.

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
        base_wkb_id = self.value % 1000
        if base_wkb_id == 1:
            return shapely.Point()
        elif base_wkb_id == 2:
            return shapely.LineString()
        elif base_wkb_id == 3:
            return shapely.Polygon()
        elif base_wkb_id == 4:
            return shapely.MultiPoint()
        elif base_wkb_id == 5:
            return shapely.MultiLineString()
        elif base_wkb_id == 6:
            return shapely.MultiPolygon()
        elif base_wkb_id == 7:
            return shapely.GeometryCollection()
        elif base_wkb_id == 0:
            return shapely.GeometryCollection()
        else:
            raise ValueError(f"No empty implemented for {self}")

    @property
    def flatten(self):
        if math.floor(self.value / 1000) <= 0:
            # Remark: for MISSING, -1/1000 == -1
            return self
        else:
            return GeometryType(self.value % 1000)

    @property
    def has_m(self) -> bool:
        if math.floor(self.value / 1000) in (2, 3):
            return True
        else:
            return False

    @property
    def has_z(self) -> bool:
        if math.floor(self.value / 1000) in (1, 3):
            return True
        else:
            return False

    @property
    def name_camelcase(self) -> str:
        """Get the name in camel case."""
        name_result = self.name
        name_result = name_result.replace("MISSING", "Missing")
        name_result = name_result.replace("MULTI", "Multi")
        name_result = name_result.replace("POINT", "Point")
        name_result = name_result.replace("POLYGON", "Polygon")
        name_result = name_result.replace("LINESTRING", "LineString")
        name_result = name_result.replace("GEOMETRY", "Geometry")
        name_result = name_result.replace("COLLECTION", "Collection")
        name_result = name_result.replace("TRIANGLE", "Triangle")
        name_result = name_result.replace("POLYHEDRALSURFACE", "PolyhedralSurface")
        # name_result = name_result.replace("TIN", "TIN")

        return name_result

    @property
    def is_multitype(self):
        """Returns if the geometry type is a multi type."""
        base_wkb_id = self.value % 1000
        if base_wkb_id in (4, 5, 6, 7):
            # It is already single type
            return True

    @property
    def to_multitype(self):
        """Get the corresponding multitype."""
        if self.is_multitype:
            return self
        elif self.value % 1000 in (1, 2, 3):
            # For the "standard" types, point, polygon and linestring, return multi
            return GeometryType(self.value + 3)
        elif self == GeometryType.MISSING:
            raise ValueError(f"No multitype implemented for {self}")
        else:
            # For all other types, return GeometryCollection
            return GeometryType(self.value - self.value % 1000 + 7)

    @property
    def to_singletype(self):
        """Get the corresponding single type."""
        base_wkb_id = self.value % 1000
        if base_wkb_id in (0, 1, 2, 3):
            # It is already single type
            return self
        elif base_wkb_id in (4, 5, 6):
            # For the "standard" types, point, polygon and linestring, return single
            return GeometryType(self.value - 3)
        elif base_wkb_id == 7:
            return GeometryType.GEOMETRY
        else:
            raise ValueError(f"No singletype implemented for {self}")

    @property
    def to_primitivetype(self):
        """Get the corresponding primitive type."""
        base_wkb_id = self.value % 1000
        if base_wkb_id in (1, 4):
            return PrimitiveType.POINT
        elif base_wkb_id in (2, 5):
            return PrimitiveType.LINESTRING
        elif base_wkb_id in (3, 6):
            return PrimitiveType.POLYGON
        elif base_wkb_id in (0, 7):
            return PrimitiveType.GEOMETRY
        else:
            raise ValueError(f"No primitivetype implemented for {self}")


class PrimitiveType(enum.Enum):
    """Enumeration of the different existing primitive types of a geometry."""

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
