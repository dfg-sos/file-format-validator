from typing import Any

from eo_format_validator.integration.handler.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_result import ValidationResult


class HTTPResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for an HTTP request."""

    def handle_success(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_failure(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Any:
        pass

