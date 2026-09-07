from typing import Optional
from abc import abstractmethod
from dataclasses import dataclass
from pyproj import CRS
from shapely import GeometryType

from ...model import FileFormatValidator, ValidationRequest, ValidationMode, ValidationResult,Info,Warning,Cause,Error


# Mapping from lowercase geometry type names (e.g. GeoJSON's "Polygon") to shapely GeometryType enum
GEOMETRY_TYPE_BY_NAME = {
    "point": GeometryType.POINT,
    "linestring": GeometryType.LINESTRING,
    "polygon": GeometryType.POLYGON,
    "multipoint": GeometryType.MULTIPOINT,
    "multilinestring": GeometryType.MULTILINESTRING,
    "multipolygon": GeometryType.MULTIPOLYGON,
    "geometrycollection": GeometryType.GEOMETRYCOLLECTION,
}


def geometry_type_from_string(type_string: str) -> Optional[GeometryType]:
    """Convert a geometry type name (e.g. GeoJSON's "Polygon") to a shapely GeometryType enum.
    Callers are responsible for not passing `None`/empty strings.
    """
    return GEOMETRY_TYPE_BY_NAME.get(type_string.lower())


@dataclass(frozen=True)
class EOMetadata:
    crs: Optional[CRS] = None
    geometry_type: Optional[GeometryType] = None

    @staticmethod
    def from_strings(crs: Optional[str] = None, geometry_type: Optional[str] = None) -> "EOMetadata":
        """Build an `EOMetadata` from plain strings, so third-party callers (e.g. an HTTP
        or CWL request builder) can compose one without importing pyproj/shapely themselves.

        Args:
            crs: Any string accepted by `pyproj.CRS.from_user_input` (e.g. "EPSG:4326", a WKT string, a proj4 string).
            geometry_type: A GeoJSON-style geometry type name (e.g. "Point", "MultiPolygon").
        """
        return EOMetadata(
            crs=CRS.from_user_input(crs) if crs else None,
            geometry_type=geometry_type_from_string(geometry_type) if geometry_type else None,
        )


def eo_metadata(request: ValidationRequest) -> EOMetadata:
    return request.metadata if isinstance(request.metadata, EOMetadata) else EOMetadata()

class EOFileFormatValidator(FileFormatValidator):
    """EO-specific validator that enables SRS validation and expects
    an `EOMetadata` sidecar on the request's `metadata` field for SRS-related checks.
    """

    @abstractmethod
    def get_crs(self,request: ValidationRequest) -> Optional[CRS]:
        pass

    def validate(self, request: ValidationRequest) -> ValidationResult:
        validation_result = super().validate(request)
        if  not isinstance(request.metadata, EOMetadata):
            return validation_result
        match request.mode:
            case ValidationMode.FULL:
                validation_result += self.assert_crs(request)
            case _:
                pass
        return validation_result

    def assert_crs(self, request:ValidationRequest) -> ValidationResult:
        actual_srs = self.get_crs(request)
        expected_srs = eo_metadata(request).crs
        if expected_srs is None:
            return ValidationResult.success(request, Info(message="No expected CRS provided, skipping CRS validation."))
        if actual_srs is None:
            return ValidationResult.uncertain(request,Warning(message="File has no CRS defined, cannot validate against expected CRS.", cause=Cause.MISSING_METADATA))
        if actual_srs != expected_srs:
            return ValidationResult.failure(request, Error(message=f"File CRS'{actual_srs}' does not match expected CRS '{expected_srs}'.", cause=Cause.METADATA_MISMATCH))
        return ValidationResult.success(request)
