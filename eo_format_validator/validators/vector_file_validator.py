from abc import abstractmethod, ABC
from typing import Optional

from .eo_file_format_validator import EOFileFormatValidator
from eo_format_validator.model import ValidationResult,GeometryType,EOValidationRequest,ValidationRequest,Error,Warning,Info,Cause,CoordinateReferenceSystem,EPSGCoordinateReferenceSystem,ValidationMode
from eo_format_validator.util import validate_crs_with_fiona, open_with_fiona, validate_shape_type_with_fiona

import fiona
from fiona.errors import DriverError

class VectorFileValidator(EOFileFormatValidator, ABC):
    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        try:
            with fiona.open(str(request.actual_file.path)) as fiona_collection:
                return ValidationResult.success(request)
        except DriverError as e:
            return ValidationResult.failure(
                request,
                Error(message=f"Failed to open file '{request.actual_file.path}' with Fiona:\n{str(e)}", cause=Cause.FILE_OPEN_ERROR)
            )
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Unknown exception occurred while opening '{request.actual_file.path}' with Fiona:\n{exc.__class__}:{str(exc)}", cause=Cause.FILE_OPEN_ERROR)
            )

    def get_crs(self, request: EOValidationRequest) -> Optional[CoordinateReferenceSystem]:
        try:
            with fiona.open(request.actual_file.path) as fiona_collection:
                crs = fiona_collection.crs
                return EPSGCoordinateReferenceSystem(crs.to_epsg()) if crs else None
        except Exception as e:
            return None
        
    @staticmethod
    def to_geometry_type(name: str) -> Optional[GeometryType]:
        if name:
            name = str(name).strip().lower()
            match name:

                case "point":
                    return GeometryType.POINT
                case "multipoint" | "multi point":
                    return GeometryType.MULTIPOINT
                case "linestring" | "line string" | "line":
                    return GeometryType.LINESTRING
                case "multilinestring" | "multi linestring" | "multi line string" | "multiline" | "multi line":
                    return GeometryType.MULTILINESTRING
                case "polygon":
                    return GeometryType.POLYGON
                case "multipolygon" | "multi polygon":
                    return GeometryType.MULTIPOLYGON
                case "triangle":
                    return GeometryType.TRIANGLE
                case "polyhedralsurface" | "polyhedral surface":
                    return GeometryType.POLYHEDRALSURFACE
                case "tin" | "triangulated irregular network":
                    return GeometryType.TIN
                case "geometrycollection" | "geometry collection":
                    return GeometryType.GEOMETRYCOLLECTION
                case _:
                    pass
        return None


    def assert_geometry_type(self,request: EOValidationRequest) -> ValidationResult:
        try:
            with fiona.open(str(request.actual_file.path)) as src:
                schema = src.schema
                actual_geometry_type = VectorFileValidator.to_geometry_type(schema.get('geometry', None)) # type: ignore
                if not actual_geometry_type:
                    return ValidationResult.uncertain(
                        request,
                        Warning(message=f"File has no geometry type defined, cannot validate against expected shape type.", cause=Cause.MISSING_METADATA)
                    )
            expected_geometry_type = request.geometry_type

            if not expected_geometry_type:
                return ValidationResult.success(
                    request,
                    Info(message=f"Geometry type '{actual_geometry_type}' detected. No expected geometry type given, skipping geometry type validation.")
                )
            if expected_geometry_type != actual_geometry_type:
                return ValidationResult.failure(
                    request,
                    Error(message=f"File geometry type '{actual_geometry_type}' does not match expected geometry type '{expected_geometry_type}'.", cause=Cause.INVALID_METADATA)
                )
            return ValidationResult.success(request)
        except Exception as e:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Unexpected error while validating geometry type:\n{str(e)}",cause = Cause.FILE_OPEN_ERROR
            ))

    def validate(self, request: ValidationRequest) -> ValidationResult:
        result = super().validate(request)
        if not isinstance(request, EOValidationRequest):
            return result
        match request.mode:
            case ValidationMode.FULL:
                result += self.assert_geometry_type(request)
            case _:
                pass
        return result.evaluate()