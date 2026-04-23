"""Well-known binary representation of geometry, binary version of WKT"""
from eo_format_validator.api.vector_file_validator import VectorFileValidator
from eo_format_validator.core.validator_registry import validators


@validators.register("format_4121")
class WKBValidator(VectorFileValidator):

    identifier: str = "formatWKB"
    #file_extensions =