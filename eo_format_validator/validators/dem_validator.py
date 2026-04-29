"""Digital Elevation Model"""
from typing import List

from ..registry import Registry 
from .raster_file_validator import RasterFileValidator

@Registry.register("format_4102")
class DEMValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        # DEMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]