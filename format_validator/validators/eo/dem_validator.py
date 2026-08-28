from typing import List

from ...registry import registry
from format_validator.model import FormatIdentifier 
from .raster_file_validator import RasterFileValidator


@registry.register(FormatIdentifier.DEM)
class DEMValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        # DEMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]