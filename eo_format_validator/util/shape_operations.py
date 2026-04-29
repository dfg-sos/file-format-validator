from unittest import expectedFailure

from eo_format_validator.model import FileInput, Format, ValidationResult,ShapeType

def normalize_geometry_to_shape_type(name: str) -> ShapeType:
    # helper: normalize type strings to ShapeTypes used across validators

    #if name.__class__.__eq__(ShapeType):
    #    return name

    if name:
        name = str(name).strip().lower()
        #print(name)
        match name:

            case "point":
                return ShapeType.POINT
            case "multipoint" | "multi point":
                return ShapeType.MULTIPOINT
            case "linestring" | "line string" | "line":
                return ShapeType.LINESTRING
            case "multilinestring" | "multi linestring" | "multi line string" | "multiline" | "multi line":
                return ShapeType.MULTILINESTRING
            case "polygon":
                return ShapeType.POLYGON
            case "multipolygon" | "multi polygon":
                return ShapeType.MULTIPOLYGON
            case "triangle":
                return ShapeType.TRIANGLE
            case "polyhedralsurface" | "polyhedral surface":
                return ShapeType.POLYHEDRALSURFACE
            case "tin" | "triangulated irregular network":
                return ShapeType.TIN
            case "geometrycollection" | "geometry collection":
                return ShapeType.GEOMETRYCOLLECTION
            case _:
                return ShapeType.OTHER

    return ShapeType.OTHER


def validate_shape_type_with_fiona(file_format: Format, input_file: FileInput,
                                   validation_result: ValidationResult) -> ValidationResult:
    """Validate the geometry type of vector files.
       Checks:
       - Geometry type is present
       - Geometry type equals expected shape type
    """

    path = input_file.get_path()

    try:
        import fiona
        from fiona.errors import DriverError
    except Exception as exc:
        validation_result.set_uncertainty(
            message=f"The validator requires the 'fiona' library to be installed.",
            code="FIONA_MISSING",
            details={"exception": str(exc)}
        )
        return validation_result

    identifier = file_format.get_identifier()
    try:
        with fiona.open(path) as src:
            schema = src.schema
            geometry_type = normalize_geometry_to_shape_type(schema.get('geometry', None))

            if not geometry_type:
                validation_result.set_uncertainty(
                    message=f"File {identifier} has no geometry type defined",
                    code="SHAPE_MISSING",
                    path=str(path)
                )
                return validation_result

            expected_shape = file_format.get_shape_type()

            if not expected_shape:
                validation_result.add_info(
                    message="Geometry type detected. No expected Shape given.",
                    code="SHAPE_FOUND",
                    details={"geometry_type": geometry_type}
                )
                return validation_result
            # Check if geometry type corresponds to shape type
            elif geometry_type == expected_shape:
                validation_result.set_success(
                    message=f"File {identifier} has a valid shape type: {geometry_type}",
                    code="SHAPE_MATCH",
                    path=str(path)
                )
                return validation_result
            else:
                # Mismatch otherwise
                validation_result.set_failure(
                    message=f"Geometry type of {identifier} does not match shape type.",
                    code="SHAPE_MISMATCH",
                    details={'shape_type': expected_shape, 'geometry_type': str(geometry_type)}
                )
                return validation_result

    except DriverError as e:
        validation_result.set_uncertainty(
            message=f"Failed to read geometry type from file: {str(e)}",
            code="SHAPE_FAILED",
            path=str(path),
            details={'error': str(e)}
        )
        return validation_result
    except Exception as e:
        validation_result.set_uncertainty(
            message=f"Unexpected error while validating geometry type: {str(e)}",
            code="SHAPE_ERROR",
            path=str(path),
            details={'error': str(e), 'error_type': type(e).__name__}
        )
        return validation_result

def compare_shape_type(expected: ShapeType, actual: ShapeType, validation_result: ValidationResult) -> ValidationResult:
    # Decide result
    if expected:
        if actual:
            if expected == actual:
                # Success
                validation_result.set_success(
                    message=f"File has a valid shape type: {actual}",
                    code="SHAPE_MATCH"
                )
            else:
                # Validation failed
                validation_result.set_failure(
                    message=f"Expected and actual shape type mismatch.",
                    code="SHAPE_MISMATCH",
                    details = {"Expected shape type": expected, "Actually found shape type:": actual}
                )
        else:
            validation_result.set_uncertainty(
                message=f"File has no shape type defined.",
                code="SHAPE_MISSING"
            )
    else:
        # no expected provided -> just report detected
        if actual:
            validation_result.add_info(
                message=f"File has a shape type: {actual}. No expected shape type was given.",
                code="SHAPE_FOUND"
            )
        else:
            validation_result.set_uncertainty(
                message=f"No shape type was given and no geometry was found. Nothing to validate.",
                code="NO_SHAPES"
            )
    return validation_result
