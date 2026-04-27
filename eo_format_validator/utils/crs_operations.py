from pathlib import Path
from typing import Union, Any

from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.model.validation_result import ValidationResult


def normalize_crs_to_epsg(crs_input: Union[int, str, Any]) -> int | None:
    """
       Attempts to extract EPSG code from various CRS input formats (EPSG code as integer or String or a CRS object).
       Returns EPSG code as integer if found, None else.
    """
    if crs_input is None:
        return None

    # If already an integer, assume it is an EPSG code and return
    if isinstance(crs_input, int):
        return crs_input

    # If String, try to parse EPSG code
    if isinstance(crs_input, str):
        # Remove common prefixes and whitespace
        normalized = crs_input.upper().strip()
        normalized = normalized.replace("EPSG:", "").replace("EPSG", "").strip()

        try:
            return int(normalized)
        except ValueError:
            # Not a simple EPSG code string
            return None

    # If CRS object (from RasterIO or similar), try to get EPSG code
    if hasattr(crs_input, 'to_epsg'):
        try:
            return crs_input.to_epsg()
        except Exception:
            return None

    # If dict with 'init' key (common CRS format)
    if isinstance(crs_input, dict) and 'init' in crs_input:
        init = crs_input['init']
        if isinstance(init, str) and 'EPSG' in init.upper():
            try:
                return int(init.split(':')[1])
            except (ValueError, IndexError):
                return None

    # Otherwise, could not determine EPSG code
    return None

def compare_crs(crs, file_format: Format, path: Path, validation_result: ValidationResult) -> ValidationResult:
    """Accesses and compares actual and expected CRS as EPSG codes.
       Does not require CRS to be present, ensure in respective validator classes if required."""

    actual_crs_epsg = normalize_crs_to_epsg(crs)
    expected_crs_epsg = file_format.get_expected_crs_epsg()
    details = {}
    if hasattr(crs, 'to_dict'):
        try:
            details = crs.to_dict()
        except Exception:
            details = {"crs_repr": str(crs)}
    if expected_crs_epsg and actual_crs_epsg is None:
        validation_result.set_uncertainty(
            message=f"File has no EPSG code defined.",
            code="EPSG_MISSING",
            path=str(path))
    elif expected_crs_epsg is None and actual_crs_epsg:
        validation_result.add_info(
            message=f"File {path} has a CRS: EPSG:{actual_crs_epsg}. No expected EPSG code was given.",
            code="EPSG_FOUND",
            details=details
        )
    elif expected_crs_epsg is None and actual_crs_epsg is None:
        validation_result.add_info(
            message=f"No CRS found for file {path} and no expected CRS given. Nothing to validate.",
            code="NO_CRS",
            details=details
        )
    elif actual_crs_epsg != expected_crs_epsg:
        validation_result.set_failure(
            message=f"Format CRS and file CRS mismatch.",
            code="CRS_MISMATCH",
            path=str(path),
            details={"File EPSG": actual_crs_epsg, "Expected EPSG:": expected_crs_epsg}
        )
    elif actual_crs_epsg == expected_crs_epsg:
        # Success
        validation_result.set_success(
            message=f"File {path} has valid CRS: EPSG:{actual_crs_epsg}",
            code="CRS_MATCH",
            details=details
        )
    return validation_result

def validate_crs_with_fiona(file_format: Format, input_file: FileInput, validation_result: ValidationResult) -> ValidationResult:
    """
       Validate that the GeoPackage has a valid CRS.
       Checks:
        - CRS is present
        - EPSG code is available (if applicable)
        - If expected_crs is set: validates that found CRS matches expected CRS
    """
    path = input_file.get_path()
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
        with fiona.open(path) as src:
            crs = src.crs

            # 1. Check: CRS must be present
            if not crs:
                validation_result.set_uncertainty(
                    message=f"File has no CRS defined.",
                    code="CRS_MISSING",
                    path=str(path)
                )
                return validation_result

            return compare_crs(crs, file_format, path, validation_result)

    except DriverError as e:
        validation_result.set_uncertainty(
            message=f"Failed to read CRS from file: {str(e)}",
            code="CRS_FAILED",
            path=str(path),
            details={'error': str(e)}
        )
        return validation_result
    except Exception as e:
        validation_result.set_uncertainty(
            message=f"Unexpected error while validating CRS: {str(e)}",
            code="CRS_ERROR",
            path=str(path),
            details={'error': str(e), 'error_type': type(e).__name__}
        )
        return validation_result




