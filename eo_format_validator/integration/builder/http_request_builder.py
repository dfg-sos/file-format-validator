from typing import Any, List

from eo_format_validator.api.validation_request import ValidationRequest
from eo_format_validator.integration.builder.validation_request_builder import ValidationRequestBuilder


class HTTPRequestBuilder(ValidationRequestBuilder):
    """Build ValidationRequests from HTTP requests."""

    def build(self) -> ValidationRequest:
        pass



