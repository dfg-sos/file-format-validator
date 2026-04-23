from typing import Dict, List, Any

from eo_format_validator.api.validation_request import ValidationRequest
from eo_format_validator.integration.builder.cwl_utils_request_builder import CWLUtilsRequestBuilder
from eo_format_validator.integration.builder.cwltool_request_builder import CWLToolRequestBuilder
from eo_format_validator.integration.handler.cwl_utils_response_handler import CWLUtilsResponseHandler
from eo_format_validator.integration.handler.cwltool_response_handler import CWLToolResponseHandler
from eo_format_validator.main.eo_validator_main import EOValidator
from eo_format_validator.result.validation_result import ValidationResult


class Validator:

    @staticmethod
    def _execute_validation(builder, handler) -> Any: #Dict[
        #str, str | None | dict[str, int] | list[dict[str, Any]]]:
        """Generic execution logic for all clients."""

        validation_result = ValidationResult()
        try:
            validation_request: ValidationRequest = builder.build()
        except ValueError as e:
            validation_result.set_failure(message="File has invalid path or secondary path.", code="PATH_ERROR",
                                          details={"details": str(e)})
            return handler.handle_failure(validation_result)
        except Exception as e:
            validation_result.add_warning(message="Unexpected error during validation.", code="BUILD_ERROR", details={"details":str(e)})
            return handler.handle_exception(e, validation_result)
        try:
            validation_result = EOValidator.validate(validation_request) # actual validation
        except Exception as e:
            validation_result.add_warning(message="Unexpected error during validation.", code="VALIDATION_ERROR",
                                          details={"details": str(e)})
            return handler.handle_exception(e, validation_result)
        if validation_result.is_valid:
            return handler.handle_success(validation_result)
        else:
            return handler.handle_failure(validation_result)


    @staticmethod
    def execute_cwl_utils_validation(location: str, secondary_files: List[str], input_format: str, config=None) ->  Dict[str, Any]: # , config: Dict[str,str] Rückgabe wie cwl utils
        """Dedicated method for cwl-utils integration in file_formats.py 'check_format'."""
        if config is None:
            config = {}
        builder = CWLUtilsRequestBuilder(location, secondary_files, input_format, config)
        handler = CWLUtilsResponseHandler()
        return Validator._execute_validation(builder, handler)

    @staticmethod
    def execute_cwltool_validation(source_data):
        """Dedicated method for cwltool integration. Call this method with cwltool objects."""
        builder = CWLToolRequestBuilder()
        handler = CWLToolResponseHandler()
        Validator._execute_validation(builder, handler)

    @staticmethod
    def execute_http_validation(source_data):
        """HTTP example."""
        #builder = HTTPRequestBuilder()
        #handler = HTTPResponseHandler()
        #Validator._execute_validation(builder, handler)
        pass
