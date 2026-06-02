from abc import ABC
from enum import Enum

class GeometryType(Enum):
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


class CoordinateReferenceSystem(ABC):
    def code(self) -> int:
        ...

    def __eq__(self, other):
        if not isinstance(other, CoordinateReferenceSystem):
            return False
        return self.code() == other.code()

    def __str__(self):
        return f"EPSG:{self.code()}"

class EPSGCoordinateReferenceSystem(CoordinateReferenceSystem):
    def __init__(self, epsg_code: int):
        self.epsg_code = epsg_code

    def code(self) -> int:
        return self.epsg_code
    
class CoordinateReferenceSystemEnumMeta(type(Enum),type(CoordinateReferenceSystem)):
    pass    

class CustomCoordinateReferenceSystem(CoordinateReferenceSystem,Enum,metaclass=CoordinateReferenceSystemEnumMeta):
    WGS84 = 4326
    MERCATOR = 3857

    def code(self) -> int:
        return int(self.value)