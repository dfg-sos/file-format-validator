from pathlib import Path
from typing import List

from .raster_file_validator import RasterFileValidator
from ...registry import registry
from format_validator.model import FormatIdentifier

@registry.register(FormatIdentifier("geotiff"))
class GeoTIFFValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']
