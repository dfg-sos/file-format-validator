from enum import Enum

class ShapeType(Enum):
    """References shape types as WKT geometries."""

    POINT = "point"
    MULTIPOINT = "multipoint"
    LINESTRING = "linestring"
    MULTILINESTRING = "multilinestring"
    POLYGON = "polygon"
    MULTIPOLYGON = "multipolygon"
    TRIANGLE = "triangle"
    POLYHEDRALSURFACE = "polyhedralsurface"
    TIN = "tin" # triangulated irregular network
    GEOMETRYCOLLECTION = "geometrycollection"
    OTHER = "other"