from typing import List

from ...registry import registry
from eo_format_validator.model import FormatIdentifier 
from .raster_file_validator import RasterFileValidator


@registry.register(FormatIdentifier("dsm"))
class DSMValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        # DSMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]

