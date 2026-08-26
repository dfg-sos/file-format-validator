from typing import List

from ...registry import registry
from eo_format_validator.model import FormatIdentifier 
from .raster_file_validator import RasterFileValidator

@registry.register(FormatIdentifier("dtm"))
class DTMValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        # DTMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]

