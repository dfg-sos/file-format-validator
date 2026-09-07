from typing import Optional
from abc import abstractmethod
from dataclasses import dataclass
from pyproj import CRS
from shapely import GeometryType

from ...model import FileFormatValidator, ValidationRequest, ValidationMode, ValidationResult,Info,Warning,Cause,Error


@dataclass(frozen=True)
class EOMetadata:
    crs: Optional[CRS] = None
    geometry_type: Optional[GeometryType] = None


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
