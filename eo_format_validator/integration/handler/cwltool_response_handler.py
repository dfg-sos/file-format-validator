from typing import Any

from eo_format_validator.integration.handler.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_result import ValidationResult


class CWLToolResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for cwltool calls."""

    def handle_success(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_failure(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Any:
        pass

