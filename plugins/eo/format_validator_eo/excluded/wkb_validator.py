"""Well-known binary representation of geometry, binary version of WKT"""
from format_validator.validators.vector_file_validator import VectorFileValidator
from format_validator.registry import validators


@validators.register("format_4121")
class WKBValidator(VectorFileValidator):

    identifier: str = "formatWKB"
    #file_extensions =