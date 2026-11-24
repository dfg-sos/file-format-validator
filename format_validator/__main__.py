"""``python -m format_validator``: the command line interface, see ``format_validator.cli.app``."""
import sys

from .cli import main

sys.exit(main())
