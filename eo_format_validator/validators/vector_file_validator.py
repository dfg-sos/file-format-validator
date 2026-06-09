from abc import ABC
from typing import Optional
from pyproj import CRS
from shapely import GeometryType
import fiona
from fiona.errors import DriverError

from .eo_file_format_validator import EOFileFormatValidator,EOValidationRequest
from eo_format_validator.model import ValidationResult,ValidationRequest,Error,Warning,Info,Cause,ValidationMode


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

    def get_crs(self, request: EOValidationRequest) -> Optional[CRS]:
        try:
            with fiona.open(request.actual_file.path) as fiona_collection:
                crs = fiona_collection.crs
                return CRS.from_epsg(crs.to_epsg()) if crs and crs.to_epsg() else None
        except Exception as e:
            return None

    def assert_geometry_type(self,request: EOValidationRequest) -> ValidationResult:
        try:
            with fiona.open(str(request.actual_file.path)) as src:
                schema = src.schema
                actual_geometry_type = GeometryType(schema.get('geometry', None)) if schema and schema.get('geometry') else None
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
                    Error(message=f"File geometry type '{actual_geometry_type}' does not match expected geometry type '{expected_geometry_type}'.", cause=Cause.METADATA_MISMATCH)
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
        return result