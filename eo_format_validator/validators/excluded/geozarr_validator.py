"""Specification: https://github.com/zarr-developers/geozarr-spec
   https://www.ogc.org/de/announcement/ogc-forms-new-geozarr-standards-working-group-to-establish-a-zarr-encoding-for-geospatial-data/"""
from typing import List

from eo_format_validator.api.raster_file_validator import RasterFileValidator
from eo_format_validator.core.file_input import FileInput
from eo_format_validator.core.format import Format
from eo_format_validator.core.validator_registry import validators
from eo_format_validator.result.validation_result import ValidationResult


@validators.register("format_4110")
class GeoZarrValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.zarr', '.zarray', 'zattrs', '.zgroup'] #no official specification, using zarr file extensions and structure

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        pass

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        pass