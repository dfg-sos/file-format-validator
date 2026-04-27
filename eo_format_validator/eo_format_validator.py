from eo_format_validator.integration.cwl import CWLUtilsRequestBuilder, CWLUtilsResponseHandler
from eo_format_validator.model.validation_request_builder import ValidationRequestBuilder
from eo_format_validator.model.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.validator_registry import validators
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.loader import load_validators_from_package
from typing import Any, Dict, List


class EOFormatValidator:
    """Entry point. Main EO validator module to execute. Orchestrator.
    Selects validator, executes validation, and always returns a ValidationResult.
    Requires a file and an identifier code.
    Provides a ValidationResult for the given ValidationRequest."""


    @staticmethod
    def _validate(validation_request: ValidationRequest) -> ValidationResult:

        # 0) REQUIRED imports of validators, triggering registration with validators
        load_validators_from_package("eo_format_validator.validators", False, False)

        # 1) Ensure ValidationRequest is not None -> setzen voraus

        # 1) Access parameters
        file_format = validation_request.get_file_format()
        file_input = validation_request.get_file_input()
        validation_mode = validation_request.get_validation_mode()

        # 2) Choose correct validator
        validator = validators.choose_and_instantiate(file_format)

        if validator is None:
            validation_result = ValidationResult()
            validation_result.add_warning(message=f"Could not validate, file format not supported.",
                                          code="NOT_SUPPORTED")
            #validation_result.set_fallback()
            return validation_result

        # 3) Execute validation
        try:

            validation_result = validator.validate(file_format, file_input, validation_mode)
        except Exception as e:
            validation_result = ValidationResult()
            validation_result.add_warning(message=f"Could not validate, exception during validation: {e}.",code="NOT_VALIDATED")
            return validation_result #ValidationResult.from_exception(file_format.get_identifier(), e)
        return validation_result


    @staticmethod
    def run(requestBuilder: ValidationRequestBuilder, handler:ValidationResponseHandler) -> Any:
        """Generic execution logic for all clients."""
        validation_result = ValidationResult()
        try:
            validation_request: ValidationRequest = requestBuilder.build()
        except ValueError as e:
            validation_result.set_failure(message="File has invalid path or secondary path.", code="PATH_ERROR",
                                          details={"details": str(e)})
            return handler.handle_failure(validation_result)
        except Exception as e:
            validation_result.add_warning(message="Unexpected error during validation.", code="BUILD_ERROR", details={"details":str(e)})
            return handler.handle_exception(e, validation_result)
        try:
            validation_result = EOFormatValidator._validate(validation_request) # actual validation
        except Exception as e:
            validation_result.add_warning(message="Unexpected error during validation.", code="VALIDATION_ERROR",
                                          details={"details": str(e)})
            return handler.handle_exception(e, validation_result)
        if validation_result.is_valid:
            return handler.handle_success(validation_result)
        else:
            return handler.handle_failure(validation_result)
        
class EOFormatValidatorWrapper(EOFormatValidator):
    @staticmethod
    def cwl_validation(location: str, secondary_files: List[str], input_format: str, config=None) ->  Dict[str, Any]: # , config: Dict[str,str] Rückgabe wie cwl utils
        """Dedicated method for cwl-utils integration in file_formats.py 'check_format'."""
        if config is None:
            config = {}
        builder = CWLUtilsRequestBuilder(location, secondary_files, input_format, config)
        handler = CWLUtilsResponseHandler()
        return EOFormatValidator.run(builder, handler)