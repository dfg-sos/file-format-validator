from typing import List

from .raster_file_validator import RasterFileValidator
from ...registry import registry
from format_validator.model import FormatIdentifier


# DEMs, DSMs and DTMs are GeoTIFFs whose pixels hold heights, which the file does not declare.
@registry.register(FormatIdentifier.GEOTIFF, FormatIdentifier.DEM, FormatIdentifier.DSM, FormatIdentifier.DTM)
class GeoTIFFValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']
