from typing import List

from ...registry import registry
from format_validator.model import FormatIdentifier
from .vector_file_validator import VectorFileValidator


@registry.register(FormatIdentifier.GEOJSON)
class GeoJSONValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.geojson', '.json']