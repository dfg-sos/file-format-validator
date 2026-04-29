"""OSM JSON"""
from typing import List

from eo_format_validator.validators.vector_file_validator import VectorFileValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.registry import validators
from eo_format_validator.model.validation_result import ValidationResult


@validators.register("format_4116")
class OSMJSONValidator(VectorFileValidator):
    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        pass

    def _get_extensions(self) -> List[str]:
        pass