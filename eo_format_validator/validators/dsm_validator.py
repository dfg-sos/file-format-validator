"""Digital Surface Model"""
from typing import List

from ..registry import Registry 
from .raster_file_validator import RasterFileValidator


@Registry.register("format_4103")
class DSMValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        # DSMs are usually GeoTIFFs -> allow common raster extensions
        return [".tif", ".tiff"]

