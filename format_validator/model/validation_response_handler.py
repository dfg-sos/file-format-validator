import sys
from abc import ABC, abstractmethod
from typing import Any

from .validation_result import ValidationResult,ValidationStatus


class ValidationResponseHandler(ABC):
    """
       Abstract interface for handling responses to callers translating the ValidationResult.

       Different response handling for different clients:
           - cwltool: Raise exception and stop workflow on error, log warnings and infos
           - HTTP: Return JSON with status code
           - CLI: Print formatted text to console
    """
    def handle(self, validation_result: ValidationResult) -> Any:
        """
           Handle the ValidationResult and return a client-specific response.

               Args:
                   validation_result: ValidationResult object to handle

               Returns:
                   Client-specific response
        """
        match validation_result.status:
            case ValidationStatus.SUCCESS:
                return self.handle_success(validation_result)
            case ValidationStatus.FAILURE:
                return self.handle_failure(validation_result)
            case ValidationStatus.UNCERTAIN:
                return self.handle_uncertain(validation_result)

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
    def handle_uncertain(self, validation_result: ValidationResult) -> Any:
        """
           Handle uncertain validation results.

            Args:
                validation_result: ValidationResult object to handle

            Returns:
                Client-specific uncertain response
        """
        pass
