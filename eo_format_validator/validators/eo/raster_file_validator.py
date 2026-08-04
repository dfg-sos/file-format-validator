from abc import ABC
from typing import Optional
from pyproj import CRS
import rasterio
from rasterio.errors import RasterioIOError

from .eo_file_format_validator import EOFileFormatValidator,EOValidationRequest
from eo_format_validator.model import ValidationResult,ValidationRequest,Error,Warning,Cause


class RasterFileValidator(EOFileFormatValidator, ABC):

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        try:
            with rasterio.open(request.actual_file.path) as src:
                width = src.width
                height = src.height
                if width <= 0 or height <= 0:
                    return ValidationResult.failure(
                        request, 
                        Error(message=f"Invalid raster dimensions: {width}x{height}",cause= Cause.METADATA_MISMATCH)
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

    def get_crs(self, request: EOValidationRequest) -> Optional[CRS]:
        try:
            with rasterio.open(request.actual_file.path) as rasterGISFile:
                srs = rasterGISFile.crs
                return srs if srs else None
        except Exception as e:
                return None
