from dataclasses import dataclass, field
from typing import Optional, Any, Dict
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


@dataclass(frozen=True) #immutable objects
class Format:
    """
       Defines a file format using the following information:
       - identifier: canonical identifier
       - expected_crs_epsg: expected CRS as EPSG code (int)
       - shape_type: expected shape defined in vector files
       - extras: placeholder dict for any additional information

       Don't name variable 'format' as it would shadow built - in name 'format'
       """


    _identifier: str
    _expected_crs_epsg: Optional[int] = None
    _shape_type: Optional[ShapeType] = None
    _extras: Dict[str, Any] = field(default_factory=dict)


    def get_identifier(self) -> str:
        return self._identifier

    def get_expected_crs_epsg(self) -> Optional[int]:
        return self._expected_crs_epsg

    def get_shape_type(self) -> Optional[ShapeType]:
        return self._shape_type

    def get_extras(self) -> dict[str, Any]:
        return self._extras