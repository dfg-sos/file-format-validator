from eo_format_validator.api.validation_request import ValidationRequest
from eo_format_validator.core.validator_registry import validators
from eo_format_validator.result.validation_result import ValidationResult
from eo_format_validator.utils.loader import load_validators_from_package


class EOValidator:
    """Entry point. Main EO validator module to execute. Orchestrator.
    Selects validator, executes validation, and always returns a ValidationResult.
    Requires a file and an identifier code.
    Provides a ValidationResult for the given ValidationRequest."""


    @staticmethod
    def validate(validation_request: ValidationRequest) -> ValidationResult:

        # 0) REQUIRED imports of validators, triggering registration with validators
        load_validators_from_package("eo_format_validator.validators", False, False)

        # 1) Ensure ValidationRequest is not None -> setzen voraus

        # 1) Access parameters
        file_format = validation_request.get_file_format()
        file_input = validation_request.get_file_input()
        validation_mode = validation_request.get_validation_mode()

        # 2) Choose correct validator
        validator = validators.choose_and_instantiate(file_format)

        if validator is None:
            validation_result = ValidationResult()
            validation_result.add_warning(message=f"Could not validate, file format not supported.",
                                          code="NOT_SUPPORTED")
            #validation_result.set_fallback()
            return validation_result

        # 3) Execute validation
        try:

            validation_result = validator.validate(file_format, file_input, validation_mode)
        except Exception as e:
            validation_result = ValidationResult()
            validation_result.add_warning(message=f"Could not validate, exception during validation: {e}.",code="NOT_VALIDATED")
            return validation_result #ValidationResult.from_exception(file_format.get_identifier(), e)
        return validation_result
