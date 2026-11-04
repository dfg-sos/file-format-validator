from typing import List

from .raster_file_validator import RasterFileValidator
from format_validator.registry import registry
from . import eo_formats
from format_validator.model import FormatIdentifier


# DEMs, DSMs and DTMs are GeoTIFFs whose pixels hold heights, which the file does not declare.
@registry.register(eo_formats.GEOTIFF, eo_formats.DEM, eo_formats.DSM, eo_formats.DTM)
class GeoTIFFValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']
