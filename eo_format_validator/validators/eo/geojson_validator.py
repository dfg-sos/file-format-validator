from typing import List

from ...registry import registry
from eo_format_validator.model import FormatIdentifier
from .vector_file_validator import VectorFileValidator

@registry.register(FormatIdentifier("geojson"))
class GeoJSONValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.geojson', '.json']