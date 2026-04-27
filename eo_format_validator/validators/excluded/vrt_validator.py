"""Documentation: https://gdal.org/drivers/vector/vrt.html"""
from typing import List

from eo_format_validator.validators.raster_file_validator import RasterFileValidator
from eo_format_validator.validator_registry import validators


@validators.register("format_4120")
class VRTValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.vrt']
