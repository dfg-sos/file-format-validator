from typing import Any, Mapping, Optional
from .registry import registry
from .model import (
    ValidationRequestBuilder,
    ValidationResponseHandler,
    ValidationRequest,
    ValidationResult,
    FormatIdentifier,
    UnsupportedMetadataKeys,
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

    @staticmethod
    def supported_metadata_keys(format_identifier: FormatIdentifier) -> frozenset[str]:
        """Keys of expected metadata understood by the validator registered for the format.

        Empty if no validator is registered for the format.
        """
        cls = registry.get_validator_class(format_identifier)
        return cls().metadata_keys() if cls else frozenset()

    @staticmethod
    def parse_metadata(format_identifier: FormatIdentifier, values: Mapping[str, str]) -> Optional[object]:
        """Build the metadata sidecar object for ``ValidationRequest.metadata`` from plain strings,
        so callers don't need to know the domain's metadata object.

        Empty values count as absent. Returns ``None`` if no validator is registered for the format.

        Raises:
            UnsupportedMetadataKeys: If a key is not understood by the format's validator.
            InvalidMetadataValue: If a value cannot be parsed.
        """
        values = {key: value for key, value in values.items() if value}
        cls = registry.get_validator_class(format_identifier)
        validator = cls() if cls else None
        supported = validator.metadata_keys() if validator else frozenset()
        unknown = set(values) - supported
        if unknown:
            raise UnsupportedMetadataKeys(unknown, supported)
        return validator.parse_metadata(values) if validator else None


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
