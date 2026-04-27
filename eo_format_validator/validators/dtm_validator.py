"""Digital Terrain Model"""
from typing import List

from eo_format_validator.validators.raster_file_validator import RasterFileValidator
from eo_format_validator.validator_registry import validators


@validators.register("format_4104")
class DTMValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        # DTMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]

