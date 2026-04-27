"""Digital Surface Model"""
from typing import List

from eo_format_validator.validators.raster_file_validator import RasterFileValidator
from eo_format_validator.validator_registry import validators


@validators.register("format_4103")
class DSMValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        # DSMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]

