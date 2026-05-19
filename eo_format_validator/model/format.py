from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Dict


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


class SpatialReferenceSystem(ABC):
    def code(self) -> int:
        ...

class EPSGSpatialReferenceSystem(SpatialReferenceSystem):
    def __init__(self, epsg_code: int):
        self.epsg_code = epsg_code

    def code(self) -> int:
        return self.epsg_code
    
class SpatialReferenceSystemEnumMeta(type(Enum),type(SpatialReferenceSystem)):
    pass    

class CustomSpatialReferenceSystem(SpatialReferenceSystem,Enum,metaclass=SpatialReferenceSystemEnumMeta):
    WGS84 = 4326
    MERCATOR = 3857

    def code(self) -> int:
        return int(self.value)

@dataclass(frozen=True)
class Format:
    """
       Defines a file format using the following information:
       - identifier: canonical identifier
       - srs: spatial reference system
       - geometry_type: expected geometry type defined in vector files
       - extras: placeholder dict for any additional information
       """
    identifier: str
    srs: Optional[SpatialReferenceSystem] = None
    geometry_type: Optional[GeometryType] = None
    extras: Dict[str, Any] = field(default_factory=dict)