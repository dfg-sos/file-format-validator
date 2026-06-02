"""Digital Terrain Model"""
from typing import List

from ..registry import Registry 
from .raster_file_validator import RasterFileValidator

@Registry.register("format_4104")
class DTMValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        # DTMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]

