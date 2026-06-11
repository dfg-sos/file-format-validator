"""Documentation: https://docs.geoserver.org/latest/en/user/community/cog/cog.html
   https://www.cogeo.org/
   https://gdal.org/drivers/raster/cog.html"""
from typing import List
from rio_cogeo.cogeo import cog_validate

from eo_format_validator.model import ValidationRequest,ValidationResult,Error,Warning,Cause
from .raster_file_validator import RasterFileValidator
from ..registry import Registry



@Registry.register("format_4100")
class COGValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        """
           This method uses the official rio-cogeo library.
           It provides more detailed COG validation
        """
        try:
            is_valid, errors, warnings = cog_validate(str(request.actual_file.path))
            result = ValidationResult(request)
            for error in errors:
                result.set_failure(
                    Error(message=f"Rio-cogeo error: {error}", cause=Cause.STRUCTURAL_MALFORMED)
                )

            for warning in warnings:
                result.set_uncertainty(
                    Warning(message=f"Rio-cogeo warning: {warning}", cause=Cause.STRUCTURAL_MALFORMED)
                )
            if is_valid:
                result.set_success()
            return result
        except Exception as e:
            return ValidationResult.failure(
                request,
                Error(message=f"Rio-cogeo validation failed for file {request.actual_file.path}: \n{str(e)}", cause=Cause.UNKNOWN)
            )


