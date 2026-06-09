from typing import Optional
from abc import abstractmethod
from attr import dataclass
from pyproj import CRS
from shapely import GeometryType

from ..model import FileFormatValidator, ValidationRequest, ValidationMode, ValidationResult,Info,Warning,Cause,Error


@dataclass(frozen=True)
class EOValidationRequest(ValidationRequest):
    crs: Optional[CRS] = None
    geometry_type: Optional[GeometryType] = None

    def enabled_modes(self) -> list[ValidationMode]:
        return super().enabled_modes() + [ValidationMode.CRS]

class EOFileFormatValidator(FileFormatValidator):
    """EO-specific validator that enables SRS validation mode and expects
    an `EOValidationRequest` for SRS-related checks.
    """

    @abstractmethod
    def get_crs(self,request: EOValidationRequest) -> Optional[CRS]:
        pass

    def validate(self, request: ValidationRequest) -> ValidationResult:
        validation_result = super().validate(request)
        if  not isinstance(request, EOValidationRequest):
            return validation_result
        match request.mode:
            case ValidationMode.CRS | ValidationMode.FULL:
                validation_result += self.assert_crs(request)
            case _: 
                pass
        return validation_result.evaluate()

    def assert_crs(self, request:EOValidationRequest) -> ValidationResult:
        actual_srs = self.get_crs(request)
        expected_srs = request.crs
        if expected_srs is None: 
            return ValidationResult.success(request, Info(message="No expected CRS provided, skipping CRS validation."))
        if actual_srs is None:
            return ValidationResult.uncertain(request,Warning(message="File has no CRS defined, cannot validate against expected CRS.", cause=Cause.MISSING_METADATA))
        if actual_srs != expected_srs:
            return ValidationResult.failure(request, Error(message=f"File CRS'{actual_srs}' does not match expected CRS '{expected_srs}'.", cause=Cause.METADATA_MISMATCH))
        return ValidationResult.success(request)
