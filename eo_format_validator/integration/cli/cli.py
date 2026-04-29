from typing import Any, List

from eo_format_validator.model.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.model.validation_request_builder import ValidationRequestBuilder
from eo_format_validator.model.validation_result import ValidationResult


class CLIRequestBuilder(ValidationRequestBuilder):
    """Build ValidationRequests from CLI arguments."""

    def build(self) -> ValidationRequest:
        pass


class CLIResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for a CLI call."""

    def handle_success(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_failure(self, validation_result: ValidationResult) -> Any:
        pass

    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Any:
        pass


def main() -> int:
    """Minimal CLI entrypoint. Keeps console-script target stable.
    This is intentionally minimal: it provides a --version flag and help text.
    Implement full CLI behavior in this module when ready.
    """
    import argparse
    from importlib.metadata import version, PackageNotFoundError

    parser = argparse.ArgumentParser(prog="eo-format-validator", description="Validate files against EO formats")
    parser.add_argument("--version", action="store_true", help="Print package version")
    args = parser.parse_args()

    if args.version:
        try:
            print(version("eo-format-validator"))
        except PackageNotFoundError:
            print("eo-format-validator (local)")
        return 0

    parser.print_help()
    return 0
