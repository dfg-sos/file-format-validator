"""Documentation: https://docs.geoserver.org/latest/en/user/community/cog/cog.html
   https://www.cogeo.org/
   https://gdal.org/drivers/raster/cog.html"""
from typing import List

from eo_format_validator.api.raster_file_validator import RasterFileValidator
from eo_format_validator.core.file_input import FileInput
from eo_format_validator.core.format import Format
from eo_format_validator.core.validator_registry import validators
from eo_format_validator.result.validation_result import ValidationResult


@validators.register("format_4100")
class COGValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']

    def _validate_open(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        """For best performance, only checks whether file can be opened and basic parameters can be accessed.
           Avoids importing RasterIO at module import time to keep the package importable
           even when RasterIO is not installed."""
        identifier = file_format.get_identifier()
        try:
            from rasterio import RasterioIOError
            import rasterio
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"The {identifier} validator requires the 'RasterIO' library to be installed.",
                code="RASTERIO_MISSING",
                details={"exception": str(exc)}
            )
            return validation_result

        path = file_input.get_path()
        try:
            with rasterio.open(path) as src:
                width = src.width
                height = src.height
                if width <= 0 or height <= 0:
                    validation_result.set_failure(
                        message=f"Invalid raster dimensions: {width}x{height}",
                        code="INVALID_DIMENSIONS",
                        path=str(path),
                        details={'width': width, 'height': height}
                    )
                    return validation_result
                cog_details = {}

                # file must be tiled (not striped)
                is_tiled = src.profile.get('tiled', False)
                blockx_size = src.profile.get('blockxsize', 0)
                blocky_size = src.profile.get('blockysize', 0)

                cog_details['is_tiled'] = is_tiled
                cog_details['tile_size'] = f"{blockx_size}x{blocky_size}"

                if not is_tiled:
                    validation_result.set_failure(
                    message=f"COG must be tiled, but file {identifier} is striped",
                    code="NOT_TILED",
                    path=str(path),
                    details=cog_details
                    )
                    return validation_result
                else:
                    validation_result.set_success(message=f"File {identifier} successfully opened with RasterIO.",
                                                  code="OPEN_PASSED",
                                                  details=cog_details)
                    return validation_result
        except RasterioIOError as e:
            validation_result.set_failure(
                message=f"Failed to open file {identifier} with RasterIO: {str(e)}",
                code="OPEN_FAILED",
                path=str(path),
                details={'error': str(e)}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not open raster file {identifier}: '{path}'.",
                code="OPEN_ERROR",
                path=str(path),
                details={"exception": str(exc)}
            )
            return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """
        Same requirements as regular GeoTIFF.
        COGValidator inherits standard CRS validation from RasterFileValidator.
        """
        return super()._validate_crs(file_format, file_input, validation_result)


    def _validate_strict(self, file_format: Format, file_input: FileInput,
                         validation_result: ValidationResult) -> ValidationResult:
        self._validate_extension(file_format, file_input, validation_result)
        self._validate_open(file_format, file_input, validation_result)
        self._validate_crs(file_format, file_input, validation_result)

        # optional, official cog checking method. Otherwise, rely on tiled vs. striped in _validate_open()
        self._validate_with_rio_cogeo(file_format, file_input, validation_result)

        # decide validated status according to unfinished validation steps: one uncertainty invalidates other validated partial results
        if validation_result.get_validated() and validation_result.get_uncertain() and validation_result.is_valid:
            validation_result.invalidate()

        return validation_result

    # ----------------------optional further advanced checks-----------------------
    def _validate_with_rio_cogeo(self, file_format: Format, file_input: FileInput,
                                 validation_result: ValidationResult) -> ValidationResult:
        """
           Optional: Use rio-cogeo library for comprehensive COG validation.

           This method uses the official rio-cogeo library if available.
           It provides more detailed COG validation

           Note: Requires 'rio-cogeo' package, not listed in requirements.txt.
        """
        identifier = file_format.get_identifier()
        try:
            from rio_cogeo.cogeo import cog_validate
            from rio_cogeo.profiles import cog_profiles

            path = str(file_input.get_path())

            # validate with rio-cogeo
            is_valid, errors, warnings = cog_validate(path)

            # include results to ValidationResult categories
            if is_valid:
                validation_result.set_success(
                    message=f"File {identifier} passed rio-cogeo validation",
                    code="RIO_PASSED"
                )
            else:
                for error in errors:
                    validation_result.set_failure(
                        message=f"Rio-cogeo error for file {identifier}: {error}",
                        code="RIO_ERROR"
                    )

            for warning in warnings:
                validation_result.set_uncertainty(
                    message=f"Rio-cogeo warning for file {identifier}: {warning}",
                    code="RIO_WARNING"
                )
        except ImportError:
            validation_result.set_uncertainty(
                message="Rio-cogeo library has to be installed for advanced COG validation.",
                code="RIO_MISSING"
            )
        except Exception as e:
            validation_result.set_uncertainty(
                message=f"Rio-cogeo validation failed for file {identifier}: {str(e)}",
                code="RIO_FAILED"
            )

        return validation_result
