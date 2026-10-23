"""Public API: list the supported formats, build a request and validate it.

Exceptions mean the request is wrong (``InvalidRequest`` and its subclasses), the ``ValidationResult``
says something about the file.
"""
from typing import Mapping, Optional
from .registry import registry
from .model import (
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
    ValidationMode,
    FormatIdentifier,
    FileInput,
    FileFormatValidator,
    UnsupportedFormat,
    UnsupportedMetadataKeys,
    Info,
    Warning,
    Error,
    Cause,
)


def supported_formats() -> list[FormatIdentifier]:
    """Formats with a registered validator, and abstract formats with a registered validator for any of their leaves."""
    abstract = [fi for fi in FormatIdentifier.all() if fi.is_abstract and _leaf_validators(fi)]
    return sorted({*registry.get_registered_identifiers(), *abstract})


def metadata_keys(format_identifier: FormatIdentifier) -> frozenset[str]:
    """Keys of expected metadata understood by the validator registered for the format.

    For an abstract format, the keys that all its leaves understand. Empty for unsupported formats.
    """
    validators = _validators(format_identifier)
    return frozenset.intersection(*(validator.metadata_keys() for validator in validators)) if validators else frozenset()


def build_request(
    format_identifier: FormatIdentifier,
    actual_file: FileInput,
    mode: ValidationMode,
    expected_metadata: Optional[Mapping[str, str]] = None,
) -> ValidationRequest:
    """Build a ``ValidationRequest`` from plain values. The files are not read.

    ``expected_metadata`` is parsed into the metadata object of the format's validator, so callers
    don't need to know the domain's metadata object. Empty values count as absent. Without values,
    a validator with metadata keys still gets an empty metadata object.

    Raises:
        UnsupportedFormat: If no validator is registered for the format or, for an abstract format, its leaves.
        UnsupportedMode: If the mode is not enabled for the request.
        UnsupportedMetadataKeys: If a key is not understood by the format's validator, or by all leaves of an abstract format.
        InvalidMetadataValue: If a value cannot be parsed.
    """
    validators = _validators(format_identifier)
    if not validators:
        raise UnsupportedFormat(format_identifier)

    values = {key: value for key, value in (expected_metadata or {}).items() if value}
    supported = metadata_keys(format_identifier)
    unknown = set(values) - supported
    if unknown:
        raise UnsupportedMetadataKeys(unknown, supported)
    # The leaves of an abstract format share one metadata object (e.g. EOMetadata), so any of them can parse it.
    metadata = validators[0].parse_metadata(values)
    return ValidationRequest(format_identifier, actual_file, mode, metadata)


def validate(validation_request: ValidationRequest) -> ValidationResult:
    """Validate a single ``ValidationRequest``.

    Returns a ``ValidationResult`` for any problem with the file. Exceptions inside a validator
    become an UNCERTAIN result. An abstract format without its own validator is validated against
    its leaves, see ``_validate_abstract``.

    Raises:
        UnsupportedFormat: If no validator is registered for the format or, for an abstract format, its leaves.
    """
    format_identifier = validation_request.format_identifier
    cls = registry.get_validator_class(format_identifier)
    if cls:
        return _run(cls(), validation_request)

    leaf_validators = _leaf_validators(format_identifier)
    if not leaf_validators:
        raise UnsupportedFormat(format_identifier)
    return _validate_abstract(validation_request, leaf_validators)


def _leaf_validators(format_identifier: FormatIdentifier) -> list[tuple[FormatIdentifier, FileFormatValidator]]:
    """Validators of the formats the format expands to, sorted by format."""
    return [(leaf, cls()) for leaf in sorted(format_identifier.expand()) if (cls := registry.get_validator_class(leaf))]


def _validators(format_identifier: FormatIdentifier) -> list[FileFormatValidator]:
    """Validators that check a request for the format: its own, or those of its leaves."""
    cls = registry.get_validator_class(format_identifier)
    return [cls()] if cls else [validator for _, validator in _leaf_validators(format_identifier)]


def _run(validator: FileFormatValidator, validation_request: ValidationRequest) -> ValidationResult:
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


def _validate_abstract(
    validation_request: ValidationRequest,
    leaf_validators: list[tuple[FormatIdentifier, FileFormatValidator]],
) -> ValidationResult:
    """Valid if the file is valid for any leaf whose extension matches. Otherwise UNCERTAIN if any
    of those leaves is uncertain, else FAILURE, with the events of each of those leaves."""
    format_identifier = validation_request.format_identifier
    candidates = [(leaf, validator) for leaf, validator in leaf_validators if validator.assert_extension(validation_request)]
    if not candidates:
        extensions = sorted({ext.lower() for _, validator in leaf_validators for ext in validator.get_extensions()})
        return ValidationResult.failure(
            validation_request,
            Error(
                message=f"File extension '{validation_request.actual_file.path.suffix.lower()}' does not match "
                f"any format of '{format_identifier}', expected one of {extensions}.",
                cause=Cause.EXTENSION_MISMATCH,
            ),
        )

    results = [(leaf, _run(validator, validation_request)) for leaf, validator in candidates]
    for leaf, result in results:
        if result.status == ValidationStatus.SUCCESS:
            return result.set_success(Info(message=f"File is valid as '{leaf}', a format of '{format_identifier}'."))

    uncertain = [(leaf, result) for leaf, result in results if result.status == ValidationStatus.UNCERTAIN]
    merged = ValidationResult(validation_request)
    for leaf, result in uncertain or results:
        merged.add(Info(message=f"Validated as '{leaf}', a format of '{format_identifier}':"))
        merged += result
    return merged
