from .registry import Registry
from .model import ValidationRequestBuilder, ValidationResponseHandler, ValidationRequest, ValidationResult
from typing import Any


class EOFormatValidator:
    """Entry point. Main EO validator module to execute. Orchestrator.
    Selects validator, executes validation, and always returns a ValidationResult.
    Requires a file and an identifier code.
    Provides a ValidationResult for the given ValidationRequest."""
    registry = Registry()

    def __init__(self, requestBuilder: ValidationRequestBuilder, responseHandler:ValidationResponseHandler):
        self.requestBuilder = requestBuilder
        self.responseHandler = responseHandler

    @staticmethod
    def validate(validation_request: ValidationRequest) -> ValidationResult:
        # 1) Access parameters
        file_format = validation_request.get_file_format()
        file_input = validation_request.get_file_input()
        validation_mode = validation_request.get_validation_mode()

        # 2) Choose correct validator
        validator = EOFormatValidator.registry.choose_and_instantiate(file_format)

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

    def run(self) -> Any:
        """Generic execution logic for all clients."""
        validation_result = ValidationResult()
        try:
            validation_request: ValidationRequest = self.requestBuilder.build()
        except ValueError as e:
            validation_result.set_failure(message="File has invalid path or secondary path.", code="PATH_ERROR",
                                          details={"details": str(e)})
            return self.responseHandler.handle_failure(validation_result)
        except Exception as e:
            validation_result.add_warning(message="Unexpected error during validation.", code="BUILD_ERROR", details={"details":str(e)})
            return self.responseHandler.handle_exception(e, validation_result)
        try:
            validation_result = EOFormatValidator.validate(validation_request) # actual validation
        except Exception as e:
            validation_result.add_warning(message="Unexpected error during validation.", code="VALIDATION_ERROR",
                                          details={"details": str(e)})
            return self.responseHandler.handle_exception(e, validation_result)
        if validation_result.is_valid:
            return self.responseHandler.handle_success(validation_result)
        else:
            return self.responseHandler.handle_failure(validation_result)