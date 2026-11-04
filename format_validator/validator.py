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


def metadata_keys(format_identifier: Optional[FormatIdentifier]) -> frozenset[str]:
    """Keys of expected metadata understood by the validator registered for the format.

    For an abstract format, the keys that all formats below it understand. Empty for unsupported
    formats and for ``None``, e.g. the result of ``FormatIdentifier.get()`` for an unknown id.
    """
    if format_identifier is None:
        return frozenset()
    validators = _validators(format_identifier)
    return frozenset.intersection(*(validator.metadata_keys() for validator in validators)) if validators else frozenset()


def build_request(
    format_identifier: Optional[FormatIdentifier],
    actual_file: FileInput,
    mode: ValidationMode,
    expected_metadata: Optional[Mapping[str, str]] = None,
) -> ValidationRequest:
    """Build a ``ValidationRequest`` from plain values. The files are not read.

    ``expected_metadata`` is parsed into the metadata object of the format's validator, so callers
    don't need to know the domain's metadata object. Empty values count as absent. Without values,
    a validator with metadata keys still gets an empty metadata object.

    ``format_identifier`` may be ``None``, so the result of ``FormatIdentifier.get()`` can be passed
    directly.

    Raises:
        UnsupportedFormat: If the format is ``None``, or no validator is registered for the format or, for an abstract format, any format below it.
        UnsupportedMode: If the mode is not enabled for the request.
        UnsupportedMetadataKeys: If a key is not understood by the format's validator, or by all formats below an abstract format.
        InvalidMetadataValue: If a value cannot be parsed.
    """
    if format_identifier is None:
        raise UnsupportedFormat(None)
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


def _validated_leaves(format_identifier: FormatIdentifier) -> list[FormatIdentifier]:
    """The most general formats with a validator below an abstract format.

    The walk down the children stops at a format with a validator: its children refine it, so a
    file valid as one of them is valid as the format too (e.g. a COG is a GeoTIFF). A format that
    is not abstract only covers itself.
    """
    if not format_identifier.is_abstract:
        return [format_identifier]
    found, seen, stack = [], set(), list(format_identifier.children)
    while stack:
        child = stack.pop()
        if child in seen:
            continue
        seen.add(child)
        if registry.get_validator_class(child):
            found.append(child)
        else:
            stack.extend(child.children)
    return found


def _leaf_validators(format_identifier: FormatIdentifier) -> list[tuple[list[FormatIdentifier], FileFormatValidator]]:
    """Validators of the formats the format covers, see ``_validated_leaves``, each with the formats
    it validates, so a validator registered for several formats (e.g. GeoTIFF and DEM) runs once.
    Its own identifier comes first, see ``registry.register``. Sorted by that identifier."""
    leaves_by_class: dict[type[FileFormatValidator], list[FormatIdentifier]] = {}
    for leaf in _validated_leaves(format_identifier):
        if cls := registry.get_validator_class(leaf):
            leaves_by_class.setdefault(cls, []).append(leaf)
    grouped = [
        (sorted(leaves, key=lambda leaf: (leaf != registry.get_identifier_for_validator(cls), leaf)), cls())
        for cls, leaves in leaves_by_class.items()
    ]
    return sorted(grouped, key=lambda item: item[0][0])


def _validators(format_identifier: FormatIdentifier) -> list[FileFormatValidator]:
    """Validators that check a request for the format: its own, or those of its leaves."""
    cls = registry.get_validator_class(format_identifier)
    return [cls()] if cls else [validator for _, validator in _leaf_validators(format_identifier)]


def _names(leaves: list[FormatIdentifier]) -> str:
    """E.g. "'GeoTIFF' (also 'DEM', 'DSM', 'DTM')"."""
    first, *others = [f"'{leaf}'" for leaf in leaves]
    return f"{first} (also {', '.join(others)})" if others else first


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
    leaf_validators: list[tuple[list[FormatIdentifier], FileFormatValidator]],
) -> ValidationResult:
    """Valid if the file is valid for any leaf whose extension matches. Otherwise UNCERTAIN if any
    of those leaves is uncertain, else FAILURE, with the events of each of those leaves.
    Each validator runs once for all its leaves, and validation stops at the first valid one.
    """
    format_identifier = validation_request.format_identifier
    candidates = [(leaves, validator) for leaves, validator in leaf_validators if validator.assert_extension(validation_request)]
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

    results = []
    for leaves, validator in candidates:
        result = _run(validator, validation_request)
        if result.status == ValidationStatus.SUCCESS:
            return result.set_success(Info(message=f"File is valid as {_names(leaves)}, a format of '{format_identifier}'."))
        results.append((leaves, result))

    uncertain = [(leaves, result) for leaves, result in results if result.status == ValidationStatus.UNCERTAIN]
    merged = ValidationResult(validation_request)
    for leaves, result in uncertain or results:
        merged.add(Info(message=f"Validated as {_names(leaves)}, a format of '{format_identifier}':"))
        merged += result
    return merged
