#import logging
import sys
from typing import Any, Dict

from eo_format_validator.integration.handler.validation_response_handler import ValidationResponseHandler
from eo_format_validator.result.validation_result import ValidationResult


class CWLUtilsResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for cwl-utils calls.
       As per design, the ValidationResult object gets transferred into an analogous dict in every case."""

    def handle_success(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """In case of cwl-utils, success is handled within cwl-utils. Returns a dict of the ValidationResult."""
        #print(validation_result.to_dict())
        #if validation_result.get_warnings():
        #    print("Could not validate inputs.")
        #    for warning in validation_result.get_warnings():
        #        self._print_warning(warning)
        #else:
            #logger.info(f"✅ Validation successful: {validation_result.summary}")


        #infos = validation_result.get_infos()
        #for info in infos:
            #logger.info(info)
        return validation_result.to_dict()


    def handle_failure(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """In case of cwl-utils, failure is handled within cwl-utils. Returns a dict of the ValidationResult."""
        #logger.error(f"❌ Validation failed: {validation_result.summary}")

        #print(f"❌ Format validation failed: {validation_result.summary}", file=sys.stderr)

        # Print all errors to stderr
        #for error in validation_result.get_errors():
        #    self._print_error(error)

        # Print warnings too (if any)
        #if validation_result.get_warnings():
        #    for warning in validation_result.get_warnings():
        #        self._print_warning(warning)

        #for info in validation_result.get_infos():
            #logger.info(info)

        return validation_result.to_dict()
    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> Dict[str, Any]:
        """In case of cwl-utils, exceptions are handled by using validation result warnings.  Returns a dict of the ValidationResult."""
        return validation_result.to_dict()
