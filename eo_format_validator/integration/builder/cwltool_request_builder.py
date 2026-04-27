from typing import Any, List

from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.integration.builder.validation_request_builder import ValidationRequestBuilder


class CWLToolRequestBuilder(ValidationRequestBuilder):
    """Build ValidationRequests from cwltool objects."""

    def build(self) -> ValidationRequest:
        pass


