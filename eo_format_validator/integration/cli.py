from typing import Any, List

from eo_format_validator.model.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.model.validation_request_builder import ValidationRequestBuilder
from eo_format_validator.model.validation_result import ValidationResult


class CLIRequestBuilder(ValidationRequestBuilder):
    """Build ValidationRequests from CLI arguments."""

    def build(self) -> ValidationRequest:
        pass

class CLIResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for a CLI call."""

    def handle_success(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_failure(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Any:
        pass
