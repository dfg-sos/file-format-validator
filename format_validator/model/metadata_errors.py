"""Errors raised while parsing expected metadata from plain strings."""


class UnsupportedMetadataKeys(ValueError):
    """Raised when metadata keys are passed that the format's validator does not understand."""

    def __init__(self, unknown: set[str], supported: frozenset[str]):
        self.unknown = unknown
        self.supported = supported
        super().__init__(
            f"Unsupported metadata keys {sorted(unknown)}, supported keys are {sorted(supported)}."
        )


class InvalidMetadataValue(ValueError):
    """Raised when a metadata value cannot be parsed. The original exception is kept as ``__cause__``."""
