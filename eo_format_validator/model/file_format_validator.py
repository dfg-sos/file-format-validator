"""Validator interface for any file-based validation."""

from abc import ABC, abstractmethod
from typing import List

from eo_format_validator.model.validation_mode import ValidationMode
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.structural_checks import check_file_extensions


class FileFormatValidator(ABC):

    crs_extracted: int

    @abstractmethod
    def _get_extensions(self) -> List[str]:
        pass

    def validate(self, file_format: Format, file_input: FileInput, validation_mode: ValidationMode) -> ValidationResult:
        # 2) Create ValidationResult for the remaining validation process
        validation_result = ValidationResult(_source=file_format.get_identifier())
        # 3) Dispatch further checks according to ValidationMode
        match validation_mode:

            case ValidationMode.STRUCTURAL:
                return self._validate_extension(file_format, file_input, validation_result)

            case ValidationMode.CRS:
                return self._validate_crs(file_format, file_input, validation_result)  # crs only

            case ValidationMode.STRICT:
                return self._validate_strict(file_format, file_input, validation_result)  # file extension, crs, open, and shape type if available

            case _:  # Otherwise
                return validation_result

    def _validate_extension(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        if not check_file_extensions(file_input, self._get_extensions()):
            validation_result.set_failure(message=f"File extension of input file with identifier {file_format.get_identifier()}' did not match expected ones.",
                                           code="EXT_MISMATCH", path=file_input.get_path().suffix.lower(),) #details={f"File extensions expected": {self._get_extensions()}, "Actual": {file_input.get_path().suffix}})
            return validation_result
        validation_result.set_success(message=f"File extension checked.", code="EXT_PASSED")
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

        self._validate_extension(file_format, file_input, validation_result)
        self._validate_open(file_format, file_input, validation_result)
        self._validate_crs(file_format, file_input, validation_result)

        # decide validated status according to unfinished validation steps: one uncertainty invalidates other validated partial results
        if validation_result.get_validated() and validation_result.get_uncertain() and validation_result.is_valid:
            validation_result.invalidate()

        return validation_result
