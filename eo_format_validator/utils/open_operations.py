from pathlib import Path

from eo_format_validator.core.file_input import FileInput
from eo_format_validator.core.format import Format
from eo_format_validator.result.validation_result import ValidationResult

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


#def open_with_element_tree(file_format: Format, input_file: FileInput,
#                           validation_result: ValidationResult) -> ValidationResult:
#    """
#       Validate that the file can be opened using an ElementTree.
#       For best performance, only ensures that the file can be opened and is valid XML. Does not perform deep
#       structural validation.
#    """
#
#    path: Path = input_file.get_path()
#
#    try:
#        # quick parse (will raise ParseError on invalid XML)
#        tree = ET.parse(str(path))
#        root = tree.getroot()
#    except ET.ParseError as exc:
#        validation_result.set_failure(
#            message=f"XML parse error: {exc}",
#            code="OPEN_FAILED",
#            details={"exception": str(exc)}
#        )
#        return validation_result
#    except Exception as exc:
#        validation_result.add_warning(
#            message=f"Could not open/parse file: {exc}",
#            code="OPEN_ERROR",
#            details={"exception": str(exc)}
#        )
#        return validation_result
#
#    # basic sanity: check for KML tag or common namespace
#    tag = root.tag
#    tag_name = tag.split('}', 1)[-1] if '}' in tag else tag
#    if tag_name.lower() != 'kml':
#        # not strictly an error — some KMLs may omit the outer <kml> namespace in some tools,
#        # but warn the user
#        validation_result.add_warning(
#            message="Root element does not appear to be <kml> — file parsed as XML but may not be strict KML.",
#            code="NOT_STRICT_KML",
#            details={"root_tag": tag}
#        )
#
#    validation_result.set_success(
#        message="KML file parsed successfully (basic check).",
#        code="OPEN_OK"
#    )
#    return validation_result
#