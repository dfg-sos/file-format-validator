from pathlib import Path
from typing import Any, List, Dict, Optional

from eo_format_validator.model.validation_mode import ValidationMode
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.model.file_input import FileInput,MultiFileInput
from eo_format_validator.model.format import Format,ShapeType
from eo_format_validator.model.validation_request_builder import ValidationRequestBuilder
from eo_format_validator.utils.crs_operations import normalize_crs_to_epsg
from eo_format_validator.utils.shape_operations import normalize_geometry_to_shape_type
from eo_format_validator.model.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_result import ValidationResult


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


class CWLUtilsResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for cwl-utils calls.
       As per design, the ValidationResult object gets transferred into an analogous dict in every case."""

    def handle_success(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """In case of cwl-utils, success is handled within cwl-utils. Returns a dict of the ValidationResult."""
        #print(validation_result.to_dict())
        #if validation_result.get_warnings():
        #    print("Could not validate inputs.")
        #    for warning in validation_result.get_warnings():
        #        self._print_warning(warning)
        #else:
            #logger.info(f"✅ Validation successful: {validation_result.summary}")


        #infos = validation_result.get_infos()
        #for info in infos:
            #logger.info(info)
        return validation_result.to_dict()


    def handle_failure(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """In case of cwl-utils, failure is handled within cwl-utils. Returns a dict of the ValidationResult."""
        #logger.error(f"❌ Validation failed: {validation_result.summary}")

        #print(f"❌ Format validation failed: {validation_result.summary}", file=sys.stderr)

        # Print all errors to stderr
        #for error in validation_result.get_errors():
        #    self._print_error(error)

        # Print warnings too (if any)
        #if validation_result.get_warnings():
        #    for warning in validation_result.get_warnings():
        #        self._print_warning(warning)

        #for info in validation_result.get_infos():
            #logger.info(info)

        return validation_result.to_dict()
    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Dict[str, Any]:
        """In case of cwl-utils, exceptions are handled by using validation result warnings.  Returns a dict of the ValidationResult."""
        return validation_result.to_dict()
