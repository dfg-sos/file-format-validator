from typing import List

from format_validator.registry import registry
from . import eo_formats
from format_validator.model import FormatIdentifier
from .vector_file_validator import VectorFileValidator


@registry.register(eo_formats.GEOJSON)
class GeoJSONValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.geojson', '.json']