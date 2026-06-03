"""https://xdmf.org/
   Extensible data model and format, not to be confused with eXtensible Model Data Format (XMDF).
   Maybe vector?"""
from pathlib import Path
from typing import List

import xml.etree.ElementTree as ET

from eo_format_validator.validators.raster_file_validator import RasterFileValidator
from eo_format_validator.validators.vector_file_validator import VectorFileValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.registry import validators
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.crs_operations import normalize_crs_to_epsg, compare_crs


@validators.register("format_4123")
class XDMFValidator(RasterFileValidator, VectorFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.xdmf', '.xmf']

    def _validate_open(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        pass

    def assert_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        pass

    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        pass