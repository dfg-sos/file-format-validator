"""Errors raised for requests that cannot be validated. Problems with the file itself are reported in the ``ValidationResult``."""
from .format_identifier import FormatIdentifier


class InvalidRequest(ValueError):
    """Base class for errors in a validation request. Clients may subclass it for their own request errors."""


class UnsupportedFormat(InvalidRequest):
    """Raised when no validator is registered for a format or, for an abstract format, any of its leaves."""

    def __init__(self, format_identifier: FormatIdentifier):
        self.format_identifier = format_identifier
        super().__init__(f"Format '{format_identifier}' is not supported, no validator is registered for it.")


class UnsupportedMode(InvalidRequest):
    """Raised when a validation mode is not enabled for the request."""


class UnsupportedMetadataKeys(InvalidRequest):
    """Raised when metadata keys are passed that the format's validator does not understand."""

    def __init__(self, unknown: set[str], supported: frozenset[str]):
        self.unknown = unknown
        self.supported = supported
        super().__init__(
            f"Unsupported metadata keys {sorted(unknown)}, supported keys are {sorted(supported)}."
        )


class InvalidMetadataValue(InvalidRequest):
    """Raised when a metadata value cannot be parsed. The original exception is kept as ``__cause__``."""
