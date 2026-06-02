from abc import ABC, abstractmethod
from typing import List

from .validation_request import ValidationRequest,ValidationMode
from .validation_result import ValidationResult,Error, Cause 

"""Validator base class for any file-based validation."""
class FileFormatValidator(ABC):

    @abstractmethod
    def get_extensions(self) -> List[str]:
        pass

    @abstractmethod
    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        pass

    def assert_extension(self, request: ValidationRequest) -> ValidationResult:
        if not any(request.actual_file.path.suffix.lower() == ext.lower() for ext in self.get_extensions()):
            return ValidationResult.failure(request, Error(message=f"File extension of input file with suffix {request.actual_file.path.suffix.lower()} does not match expected ones for format {request.expected_format.identifier}.",cause=Cause.EXTENSION_MISMATCH))
        return ValidationResult.success(request)
    
    def assert_exists(self, request: ValidationRequest) -> ValidationResult:
        result = ValidationResult(request)
        for path in request.actual_file.files():
            if not path.exists():
                result.set_failure(Error(message=f"Input '{path}' does not exist.", cause=Cause.PATH_ERROR))
                continue
            if not path.is_file():
                result.set_failure(Error(message=f"Input '{path}' is not a file.", cause=Cause.PATH_ERROR))
        return result.evaluate() 

    def validate(self, request: ValidationRequest) -> ValidationResult:
        validation_result = ValidationResult(request)
        match request.mode:
            case ValidationMode.BASIC:
                validation_result += self.assert_extension(request=request)
            case ValidationMode.STRUCTURAL:
                validation_result += self.assert_extension(request)
                validation_result += self.assert_exists(request)
            case ValidationMode.FULL:
                validation_result += self.assert_extension(request)
                validation_result += self.assert_exists(request)
                validation_result += self.assert_can_open(request)
                # Base validator is domain-agnostic and does not perform SRS checks.
        return validation_result.evaluate()