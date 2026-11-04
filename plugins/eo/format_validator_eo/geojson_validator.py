from typing import List

from format_validator.registry import registry
from . import formats
from format_validator.model import FormatIdentifier
from .vector_file_validator import VectorFileValidator


@registry.register(formats.GEOJSON)
class GeoJSONValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.geojson', '.json']