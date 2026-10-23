"""Validate files against a format: list the supported formats, build a request and validate it.

The extension API for writing validators lives in ``format_validator.registry``,
``format_validator.model`` and ``format_validator.validators``.
"""
from .validator import supported_formats, metadata_keys, build_request, validate
from .translator import FormatTranslator
from .model import (
    # Input
    FormatIdentifier,
    FileInput,
    MultiFileInput,
    ValidationMode,
    ValidationRequest,
    # Output
    ValidationResult,
    ValidationStatus,
    Cause,
    # Request errors
    InvalidRequest,
    UnsupportedFormat,
    UnsupportedMode,
    UnsupportedMetadataKeys,
    InvalidMetadataValue,
)

# Registers the built-in validators.
from . import validators as _validators  # noqa: F401

__all__ = [
    "supported_formats",
    "metadata_keys",
    "build_request",
    "validate",
    "FormatTranslator",
    "FormatIdentifier",
    "FileInput",
    "MultiFileInput",
    "ValidationMode",
    "ValidationRequest",
    "ValidationResult",
    "ValidationStatus",
    "Cause",
    "InvalidRequest",
    "UnsupportedFormat",
    "UnsupportedMode",
    "UnsupportedMetadataKeys",
    "InvalidMetadataValue",
]
