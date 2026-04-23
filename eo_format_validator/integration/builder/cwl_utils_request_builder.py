from pathlib import Path
from typing import Any, List, Dict, Optional

from eo_format_validator.api.validation_mode import ValidationMode
from eo_format_validator.api.validation_request import ValidationRequest
from eo_format_validator.core.file_input import FileInput
from eo_format_validator.core.format import Format
from eo_format_validator.core.multi_file_input import MultiFileInput
from eo_format_validator.core.shape_type import ShapeType
from eo_format_validator.integration.builder.validation_request_builder import ValidationRequestBuilder
from eo_format_validator.utils.crs_operations import normalize_crs_to_epsg
from eo_format_validator.utils.shape_operations import normalize_geometry_to_shape_type


class CWLUtilsRequestBuilder(ValidationRequestBuilder):
    """Build ValidationRequests from cwl-utils file_formats.py."""

    def __init__(self, location: str, secondary_files: List[str], input_format: str, config: Dict[str,Any]):
        self.location: str = location
        self.secondary_files: List[str] = secondary_files
        self.input_format: str = input_format
        self.config: Dict[str,Any] = config

    def build(self) -> ValidationRequest:
        location: str = self.location
        secondary_files: List[str] = self.secondary_files
        input_format: str = self.input_format

        if "format" in input_format.lower():
            fmt = input_format.lower().find("format")
            actual_format = input_format[fmt:]  # extract format from namespace -> e.g. "format_4100"
        else:
            actual_format = input_format # default if not a valid ontology identifier

        expected_crs_epsg: Optional[int] = None
        shape_type: Optional[ShapeType] = None
        extras: Dict[str, Any] = {}
        config: Dict[str, Any] = self.config
        if config.get("crs"):
            expected_crs_epsg = normalize_crs_to_epsg(config.get("crs"))
        if config.get("shape_type"):
            shape_type = normalize_geometry_to_shape_type(config.get("shape_type"))

        if config.get("extras"):
            extras = config.get("extras")
        file_format = Format(actual_format, expected_crs_epsg, shape_type, extras)

        validation_mode: ValidationMode = ValidationMode.STRUCTURAL  # strict validation requires config parameters to be set
        if config.get("validation_mode"):
            validation_mode = ValidationMode(config.get("validation_mode").lower())

        if secondary_files:
            secondary_files_paths: List[Path] = []
            for path_str in secondary_files:
                path: Path = Path.from_uri(path_str)
                secondary_files_paths.append(path)

            input_file = MultiFileInput(Path.from_uri(location), {}, secondary_files_paths)
            return ValidationRequest(file_format, input_file, validation_mode)
        else:
            input_file = FileInput(Path.from_uri(location), {})
            return ValidationRequest(file_format, input_file, validation_mode)
