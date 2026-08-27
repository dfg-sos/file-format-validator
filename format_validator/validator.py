from typing import Any, Optional
from .registry import registry
from .model import (
    ValidationRequestBuilder,
    ValidationResponseHandler,
    ValidationRequest,
    ValidationResult,
    Warning,
    Cause,
)


class FormatValidator:
    """Entry point. Main format validator module to execute. Orchestrator.

    Selects validator, executes validation, and always returns a
    ``ValidationResult``.  Requires a file and an identifier code.
    Provides a ``ValidationResult`` for the given ``ValidationRequest``.
    """

    def __init__(
        self,
        request_builder: ValidationRequestBuilder,
        response_handler: ValidationResponseHandler,
    ):
        self.request_builder = request_builder
        self.response_handler = response_handler

    @staticmethod
    def validate(validation_request: ValidationRequest) -> ValidationResult:
        """Validate a single ``ValidationRequest``.

        Returns a ``ValidationResult`` in all cases.  Unsupported formats
        and internal exceptions are surfaced as warnings so that the caller
        can decide how to handle them.
        """
        validator = registry.choose_and_instantiate(validation_request)
        if validator is None:
            return ValidationResult.uncertain(
                validation_request,
                Warning(
                    message=f"Could not validate, file format not supported: "
                    f"'{validation_request.format_identifier}'.",
                    cause=Cause.UNKNOWN,
                ),
            )

        try:
            return validator.validate(validation_request)
        except Exception as exc:
            return ValidationResult.uncertain(
                validation_request,
                Warning(
                    message=f"Exception during validation: {exc}.",
                    cause=Cause.UNKNOWN,
                ),
            )


    def run(self) -> Any:
        """Generic execution logic for all clients.

        1. Build the request via ``request_builder.build()``.
        2. Run validation via ``validate()``.
        3. Delegate the result to the appropriate ``response_handler`` method.
        """
        validation_request: Optional[ValidationRequest] = self.request_builder.build()
        if validation_request is None:
            return self.response_handler.handle_uncertain(
                ValidationResult.uncertain(request=None, event= Warning(message="ValidationRequest could not be built.", cause=Cause.UNKNOWN)) # type: ignore
            ) 
        try:
            validation_result = FormatValidator.validate(validation_request)
            return self.response_handler.handle(validation_result)
        except Exception as exc:
            return self.response_handler.handle_uncertain(
                ValidationResult.uncertain(validation_request, Warning(message=f"Unexpected error during validation: {exc}", cause=Cause.UNKNOWN))
            )
