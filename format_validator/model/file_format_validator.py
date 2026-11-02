from abc import ABC, abstractmethod
from typing import List, Mapping, Optional

from .validation_request import ValidationRequest,ValidationMode
from .validation_result import ValidationResult, ValidationStatus, Error, Warning, Cause 

"""Validator base class for any file-based validation."""
class FileFormatValidator(ABC):

    @abstractmethod
    def get_extensions(self) -> List[str]:
        pass

    @abstractmethod
    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        pass

    def metadata_keys(self) -> frozenset[str]:
        """Keys of expected metadata this validator understands. Empty for validators without metadata."""
        return frozenset()

    def parse_metadata(self, values: Mapping[str, str]) -> Optional[object]:
        """Build the metadata sidecar object for ``ValidationRequest.metadata`` from plain strings.

        Callers have already removed empty values and checked the keys against ``metadata_keys()``.
        Validators with metadata keys return an empty metadata object for empty ``values``, so that
        skipped checks are still reported. Raises ``InvalidMetadataValue`` for values that cannot be parsed.
        """
        return None

    def assert_extension(self, request: ValidationRequest) -> ValidationResult:
        if not any(request.actual_file.path.suffix.lower() == ext.lower() for ext in self.get_extensions()):
            return ValidationResult.failure(request, Error(message=f"File extension of input file with suffix {request.actual_file.path.suffix.lower()} does not match expected ones for format {request.format_identifier}.",cause=Cause.EXTENSION_MISMATCH))
        return ValidationResult.success(request)
    
    def assert_exists(self, request: ValidationRequest) -> ValidationResult:
        result = ValidationResult(request)
        for path in request.actual_file.files():
            if not path.exists():
                result.set_failure(Error(message=f"Input '{path}' does not exist.", cause=Cause.PATH_ERROR))
                continue
            if not path.is_file():
                result.set_failure(Error(message=f"Input '{path}' is not a file.", cause=Cause.PATH_ERROR))
        return result

    def assert_metadata(self, request: ValidationRequest) -> ValidationResult:
        """Checks that read only the file's header or declarations, so their cost does not grow with the file size."""
        return self.assert_can_open(request)

    def assert_content(self, request: ValidationRequest) -> ValidationResult:
        """Read every pixel, feature or record of the file. Validators that cannot read the content report UNCERTAIN."""
        return ValidationResult.uncertain(request, Warning(message=f"Content validation is not implemented for format {request.format_identifier}, only its metadata was validated.", cause=Cause.UNKNOWN))

    def validate(self, request: ValidationRequest) -> ValidationResult:
        validation_result = ValidationResult(request)
        validation_result += self.assert_extension(request)
        if request.mode == ValidationMode.BASIC:
            return validation_result
        validation_result += self.assert_exists(request)
        validation_result += self.assert_metadata(request)
        # Skip the costly read when the cheap checks already failed
        if request.mode == ValidationMode.CONTENT and validation_result.status != ValidationStatus.FAILURE:
            validation_result += self.assert_content(request)
        return validation_result
