from .registry import registry
from .model import (
    ValidationRequestBuilder,
    ValidationResponseHandler,
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
    Warning,
    Error,
    Cause,
)
from .compatibility import FormatOntology, CompatibilityResult
from .model.format_identifier import FormatIdentifier
from .model.format_identifier import FormatIdentifier
from typing import Any, Optional


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

    @staticmethod
    def check_compatibility(
        expected_format: str,
        actual_format: str,
        ontology_source: str,
    ) -> CompatibilityResult:
        """Check whether ``actual_format`` is compatible with ``expected_format``
        according to the provided ontology.

        Compatibility is **directional**: the actual format must be the same as,
        or a subclass of, the expected format.

        Args:
            expected_format: The required/expected format identifier.
            actual_format: The available/provided format identifier.
            ontology_source: Path or URI to the ontology file.

        Returns:
            A ``CompatibilityResult`` indicating whether the formats are compatible.
        """
        try:
            ontology = FormatOntology(ontology_source)
            compatible = ontology.are_compatible(expected_format, actual_format)
            if compatible:
                msg = (
                    f"'{actual_format}' is compatible with '{expected_format}' "
                    f"according to ontology '{ontology_source}'."
                )
            else:
                msg = (
                    f"'{actual_format}' is NOT compatible with '{expected_format}' "
                    f"according to ontology '{ontology_source}'."
                )
            return CompatibilityResult(
                compatible=compatible,
                expected=expected_format,
                actual=actual_format,
                message=msg,
                ontology_source=ontology_source,
            )
        except Exception as exc:
            return CompatibilityResult(
                compatible=False,
                expected=expected_format,
                actual=actual_format,
                message=f"Error during compatibility check: {exc}",
                ontology_source=ontology_source,
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
