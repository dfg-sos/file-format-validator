from pathlib import Path

from eo_format_validator.model import FileInput, Format, ValidationResult

import xml.etree.ElementTree as ET
def open_with_fiona(file_format: Format, input_file: FileInput,
                    validation_result: ValidationResult) -> ValidationResult:
    """
       Validate that the file can be opened with Fiona.
       For best performance, only checks whether file can be opened and basic metadata is available.
       Does not extract extensive metadata.
    """

    path: Path = input_file.get_path()
    identifier = file_format.get_identifier()

    try:
        import fiona
        from fiona.errors import DriverError
    except Exception as exc:
        validation_result.set_uncertainty(
            message=f"The {identifier} validator requires the 'fiona' library to be installed.",
            code="FIONA_MISSING",
            details={"exception": str(exc)}
        )
        return validation_result

    try:
        with fiona.open(str(path)) as src:
            # Just verify file can be opened
            # Access basic properties to ensure it is readable
            _ = src.schema
            _ = src.crs

        # Success
        validation_result.set_success(
            message=f"File {identifier} successfully opened with fiona.",
            code="OPEN_PASSED"
        )
        return validation_result

    except DriverError as e:
        validation_result.set_failure(
            message=f"Failed to open {identifier} with fiona: {e}",
            code="OPEN_FAILED",
            path=str(path),
            details={"error": str(e)}
        )
        return validation_result
    except Exception as e:
        validation_result.set_uncertainty(
            message=f"Unexpected error while opening {identifier}: {e}",
            code="OPEN_ERROR",
            path=str(path),
            details={"exception": str(e)}
        )
        return validation_result