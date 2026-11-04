from typing import List

from format_validator.validators.vector_file_validator import VectorFileValidator
from format_validator.model.file_input import FileInput
from format_validator.model.format import Format
from format_validator.registry import validators
from format_validator.model.validation_result import ValidationResult


@validators.register("format_3752")
class CSVValidator(VectorFileValidator):
    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        pass

    def _get_extensions(self) -> List[str]:
        return ['.csv']