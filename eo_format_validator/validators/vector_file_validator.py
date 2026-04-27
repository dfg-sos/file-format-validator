from abc import abstractmethod, ABC

from eo_format_validator.model.file_format_validator import FileFormatValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format, ShapeType
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.crs_operations import validate_crs_with_fiona
from eo_format_validator.utils.open_operations import open_with_fiona
from eo_format_validator.utils.shape_operations import validate_shape_type_with_fiona


class VectorFileValidator(FileFormatValidator, ABC):
    """Implements _validate_open and _validate_crs using fiona as it is the required implementation for both GeoPackage and Shapefile."""

    shape_type_extracted: ShapeType

    def _validate_open(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        return open_with_fiona(file_format, file_input, validation_result)

    def _validate_crs(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        return validate_crs_with_fiona(file_format, file_input, validation_result)

    @abstractmethod
    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        return validate_shape_type_with_fiona(file_format, file_input, validation_result)

    def get_shape_type(self):
        return self.shape_type_extracted

    def _validate_strict(self, file_format: Format, file_input: FileInput,
                         validation_result: ValidationResult) -> ValidationResult:
        """Combination of all other validation methods, stacking ValidationResults. Includes shape type for vector files."""

        self._validate_extension(file_format, file_input, validation_result)
        self._validate_open(file_format, file_input, validation_result)
        self._validate_crs(file_format, file_input, validation_result)
        self._validate_shape_type(file_format, file_input, validation_result)

        # decide validated status according to unfinished validation steps: one uncertainty invalidates other validated partial results
        if validation_result.get_validated() and validation_result.get_uncertain() and validation_result.is_valid:
            validation_result.invalidate()

        return validation_result