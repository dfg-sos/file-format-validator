from typing import List

from .raster_file_validator import RasterFileValidator
from format_validator.registry import registry
from . import formats
from format_validator.model import FormatIdentifier


# DEMs, DSMs and DTMs are GeoTIFFs whose pixels hold heights, which the file does not declare.
@registry.register(formats.GEOTIFF, formats.DEM, formats.DSM, formats.DTM)
class GeoTIFFValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']
