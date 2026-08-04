from typing import List

from ...registry import registry 
from .raster_file_validator import RasterFileValidator

@registry.register("format_4102")
class DEMValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        # DEMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]