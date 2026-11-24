"""Command line interface ``format-validator``, see ``format_validator.cli.app``.

- ``app``: argument parsing, validation and exit status
- ``manifest``: the files to validate, from the arguments or a manifest
- ``printer``: the human-readable output
"""
from .app import EXIT_FAILED, EXIT_OK, EXIT_USAGE, MAPPINGS_ENV, main

__all__ = ["EXIT_FAILED", "EXIT_OK", "EXIT_USAGE", "MAPPINGS_ENV", "main"]
