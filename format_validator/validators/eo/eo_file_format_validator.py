from typing import Mapping, Optional
from abc import abstractmethod
from dataclasses import dataclass
from pyproj import CRS
from pyproj.exceptions import CRSError
from shapely import GeometryType

from format_validator.model import FileFormatValidator, ValidationRequest, ValidationMode, ValidationResult,Info,Warning,Cause,Error,InvalidMetadataValue


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


def geometry_type_from_string(type_string: str) -> GeometryType:
    """Convert a geometry type name (e.g. GeoJSON's "Polygon") to a shapely GeometryType enum.
    Callers are responsible for not passing `None`/empty strings.
    """
    result = GEOMETRY_TYPE_BY_NAME.get(type_string.lower())
    if result is None:
        raise ValueError(f"Unknown geometry type: {type_string}")
    return result


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

    def metadata_keys(self) -> frozenset[str]:
        return frozenset({"crs"})

    def parse_metadata(self, values: Mapping[str, str]) -> EOMetadata:
        # Keys are checked against metadata_keys() by the caller, so validators without
        # "geometry_type" never receive it.
        try:
            return EOMetadata.from_strings(crs=values.get("crs"), geometry_type=values.get("geometry_type"))
        except (CRSError, ValueError) as exc:
            raise InvalidMetadataValue(str(exc)) from exc

    def validate(self, request: ValidationRequest) -> ValidationResult:
        validation_result = super().validate(request)
        if request.metadata is None:
            return validation_result
        if not isinstance(request.metadata, EOMetadata):
            # Fail instead of silently skipping metadata checks, e.g. when a raw dict was passed.
            return validation_result.set_failure(Error(message=f"Metadata of type '{type(request.metadata).__name__}' is not supported for format {request.format_identifier}, expected '{EOMetadata.__name__}'.", cause=Cause.METADATA_MISMATCH))
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
