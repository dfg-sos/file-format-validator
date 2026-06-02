from typing import Optional
from abc import abstractmethod

from ..model import FileFormatValidator, ValidationRequest, EOValidationRequest, ValidationMode, ValidationResult, CoordinateReferenceSystem,Info,Warning,Cause,Error


class EOFileFormatValidator(FileFormatValidator):
    """EO-specific validator that enables SRS validation mode and expects
    an `EOValidationRequest` for SRS-related checks.
    """

    @abstractmethod
    def get_crs(self,request: EOValidationRequest) -> Optional[CoordinateReferenceSystem]:
        pass

    def validate(self, request: ValidationRequest) -> ValidationResult:
        validation_result = super().validate(request)
        if  not isinstance(request, EOValidationRequest):
            return validation_result
        match request.mode:
            case ValidationMode.CRS | ValidationMode.FULL:
                validation_result += self.assert_srs(request)
            case _: 
                pass
        return validation_result.evaluate()

    @abstractmethod
    def assert_srs(self, request:EOValidationRequest) -> ValidationResult:
        actual_srs = self.get_crs(request)
        expected_srs = request.crs
        if expected_srs is None: 
            return ValidationResult.success(request, Info(message="No expected SRS provided, skipping SRS validation."))
        if actual_srs is None:
            return ValidationResult.uncertain(request,Warning(message="File has no SRS defined, cannot validate against expected SRS.", cause=Cause.MISSING_METADATA))
        if actual_srs != expected_srs:
            return ValidationResult.failure(request, Error(message=f"File SRS'{actual_srs}' does not match expected SRS '{expected_srs}'.", cause=Cause.INVALID_METADATA))
        return ValidationResult.success(request)
