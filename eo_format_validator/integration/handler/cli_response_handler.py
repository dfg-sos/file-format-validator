from typing import Any

from eo_format_validator.integration.handler.validation_response_handler import ValidationResponseHandler
from eo_format_validator.result.validation_result import ValidationResult


class CLIResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for a CLI call."""

    def handle_success(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_failure(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Any:
        pass

