from abc import ABC, abstractmethod
from typing import List
from unittest import case

from .validation_mode import ValidationMode
from .validation_request import ValidationRequest
from .validation_result import ValidationResult
from .format import Format
from .file_input import FileInput

"""Validator interface for any file-based validation."""
class FileFormatValidator(ABC):
    @abstractmethod
    def allowed_file_extensions(self) -> List[str]:
        pass

    def validate_extension(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        if not any(file_input.path.suffix.lower() == ext.lower() for ext in self.allowed_file_extensions()):
            validation_result.set_failure(message=f"File extension of input file with identifier {file_format.identifier}' did not match expected ones.",
                                           code="EXT_MISMATCH", path=file_input.path.suffix.lower(),)
            return validation_result

        validation_result.set_success(message=f"File extension checked.", code="EXT_PASSED")
        return validation_result
    
    def validate_existence(self, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        for path in file_input.files():
            if not path.exists():
                validation_result.set_failure(message=f"Input '{path}' does not exist.", code="PATH_ERROR", path=str(path))
                continue
            if not path.is_file():
                validation_result.set_failure(message=f"Input '{path}' is not a file.", code="PATH_ERROR", path=str(path))
        return validation_result


    crs_extracted: int
    def validate(self, request: ValidationRequest) -> ValidationResult:
        validation_result = ValidationResult(source=request.expected_format.identifier)
        # 3) Dispatch further checks according to ValidationMode
        expected_format = request.expected_format
        actual_file = request.actual_file
        match request.mode:
            case ValidationMode.BASIC:
                return self.validate_extension(expected_format, actual_file, validation_result)
            case ValidationMode.STRUCTURAL:
                self.validate_extension(expected_format, actual_file, validation_result)
                self.validate_existence(actual_file, validation_result)
                validation_result.set_success(message=f"File(s) existence checked.", code="EXISTENCE_PASSED")
                return validation_result
            case ValidationMode.SRS:
                return self._validate_crs(expected_format, actual_file, validation_result)  # crs only
            case ValidationMode.FULL:
                self.validate_extension(expected_format, actual_file, validation_result)
                self.validate_existence(actual_file, validation_result)
                self._validate_open(expected_format, actual_file, validation_result)
                self._validate_crs(expected_format, actual_file, validation_result)

                # decide validated status according to unfinished validation steps: one uncertainty invalidates other validated partial results
                if validation_result.get_validated() and validation_result.get_uncertain() and validation_result.is_valid:
                    validation_result.invalidate()

                return validation_result


            case _:  # Otherwise
                return validation_result






    @abstractmethod
    def _validate_open(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        pass

    @abstractmethod
    def _validate_crs(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        """If file does not use a crs, only add info and return."""
        pass

    #@abstractmethod
    def get_crs(self) -> int:
        """Return CRS as four digit EPSG code."""
        return self.crs_extracted

    def _validate_strict(self, file_format: Format, file_input: FileInput,
                         validation_result: ValidationResult) -> ValidationResult:
        """Combination of all other validation methods, merging ValidationResults."""

        # validated hier nur true wenn alle validated wurden oder fehler gefunden und sonstiges (warnung)

