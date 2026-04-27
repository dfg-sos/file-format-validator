import sys
from abc import ABC, abstractmethod
from typing import Any

from eo_format_validator.model.validation_result import ValidationResult


class ValidationResponseHandler(ABC):
    """
       Abstract interface for handling responses to callers translating the ValidationResult.

       Different response handling for different clients:
           - cwltool: Raise exception and stop workflow on error, log warnings and infos
           - HTTP: Return JSON with status code
           - CLI: Print formatted text to console
    """

    @abstractmethod
    def handle_success(self, validation_result: ValidationResult) -> Any:
        """
           Handle successful validation (ValidationResult is valid, no errors).

               Args:
                   validation_result: ValidationResult with is_valid=True

               Returns:
                   Client-specific success response
        """
        pass

    @abstractmethod
    def handle_failure(self, validation_result: ValidationResult) -> Any:
        """
           Handle failed validation (ValidationResult contains errors).

               Args:
                   validation_result: ValidationResult with is_valid=False

               Returns:
                   Client-specific failure response
        """
        pass

    @abstractmethod
    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Any:
        """
           Handle exception during validation.

            Args:
                exception: Exception that occurred during validation process
                validation_result: ValidationResult object to handle

            Returns:
                Client-specific error response
        """
        pass

    @staticmethod
    def _print_error(error):
        """
        Print error to stderr in human-readable format.

        Format:
          ERROR [CODE]: Message
            Details: {...}
        """
        print(f"  ERROR [{error.code}]: {error.get_message()}", file=sys.stderr)

        if error.details:
            print(f"    Details: {error.details}", file=sys.stderr)

    @staticmethod
    def _print_warning(warning):
        """
        Print warning to stderr in human-readable format.

        Format:
          WARNING [CODE]: Message
        """
        print(f"  WARNING [{warning.code}]: {warning.get_message()}", file=sys.stderr)

        if hasattr(warning, 'details') and warning.details:
            print(f"    Details: {warning.details}", file=sys.stderr)
