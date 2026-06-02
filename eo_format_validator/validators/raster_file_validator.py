from abc import ABC
from typing import Optional

from .eo_file_format_validator import EOFileFormatValidator
from eo_format_validator.model import EOValidationRequest,ValidationResult,ValidationRequest,Error,Warning,Cause,CoordinateReferenceSystem,EPSGCoordinateReferenceSystem

import rasterio
from rasterio.errors import RasterioIOError

class RasterFileValidator(EOFileFormatValidator, ABC):

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        try:
            with rasterio.open(request.actual_file.path) as src:
                width = src.width
                height = src.height
                if width <= 0 or height <= 0:
                    return ValidationResult.failure(
                        request, 
                        Error(message=f"Invalid raster dimensions: {width}x{height}",cause= Cause.INVALID_METADATA)
                    )
                return ValidationResult.success(request)
        except RasterioIOError as e:
            return ValidationResult.failure(
                request,
                Error(message=f"Failed to open file '{request.actual_file.path}' with RasterIO:\n{str(e)}", cause=Cause.FILE_OPEN_ERROR)
            )
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Unknown exception occurred while opening '{request.actual_file.path}' with RasterIO:\n{exc.__class__}:{str(exc)}", cause=Cause.FILE_OPEN_ERROR)
            )

    def get_crs(self, request: EOValidationRequest) -> Optional[CoordinateReferenceSystem]:
        try:
            with rasterio.open(request.actual_file.path) as rasterGISFile:
                srs = rasterGISFile.crs
                return EPSGCoordinateReferenceSystem(srs.to_epsg()) if srs else None
        except Exception as e:
                return None
