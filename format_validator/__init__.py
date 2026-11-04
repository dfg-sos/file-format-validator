"""Validate files against a format: list the supported formats, build a request and validate it.

The core defines no formats. Plugins define format identifiers and register validators, see
``format_validator.registry.load_plugins``. The extension API for writing them lives in
``format_validator.registry`` and ``format_validator.model``.
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

from .registry import registry as _registry

# Registers the formats and validators of the installed plugins.
_registry.load_plugins()

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
