from typing import Any, List

from eo_format_validator.model.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.model.validation_request_builder import ValidationRequestBuilder


class HTTPRequestBuilder(ValidationRequestBuilder):
    """Build ValidationRequests from HTTP requests."""

    def build(self) -> ValidationRequest:
        pass


class HTTPResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for an HTTP request."""

    def handle_success(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_failure(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Any:
        pass

