"""OpenStreetMap Protocolbuffer Binary Format, OSM PBF"""
from typing import List

from eo_format_validator.api.vector_file_validator import VectorFileValidator
from eo_format_validator.core.file_input import FileInput
from eo_format_validator.core.format import Format
from eo_format_validator.core.validator_registry import validators
from eo_format_validator.result.validation_result import ValidationResult


@validators.register("format_4118")
class PBFValidator(VectorFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.osm.pbf']

    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        pass