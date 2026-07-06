from typing import List

from ..registry import Registry
from .vector_file_validator import VectorFileValidator

@Registry.register("format_4106")
class GeoJSONValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.geojson', '.json']