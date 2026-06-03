from pathlib import Path
from typing import List

from .raster_file_validator import RasterFileValidator
from ..registry import Registry

@Registry.register("format_4109")
class GeoTIFFValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']
