"""Digital Elevation Model"""
from typing import List

from eo_format_validator.api.raster_file_validator import RasterFileValidator
from eo_format_validator.core.validator_registry import validators


@validators.register("format_4102")
class DEMValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        # DEMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]