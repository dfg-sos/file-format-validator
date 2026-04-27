from abc import ABC

from eo_format_validator.model.file_format_validator import FileFormatValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.crs_operations import compare_crs


class RasterFileValidator(FileFormatValidator, ABC):

    def _validate_open(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        """For best performance, only checks whether file can be opened and basic parameters can be accessed.
           Avoids importing RasterIO at module import time to keep the package importable
           even when RasterIO is not installed."""
        identifier = file_format.get_identifier()
        try:
            import rasterio
            from rasterio.errors import RasterioIOError
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
                #profile = src.profile
                #driver = profile.get("driver") if profile is not None else getattr(src, "driver", None)

                width = src.width
                height = src.height
                if width <= 0 or height <= 0:
                    validation_result.set_failure(
                        message=f"Invalid raster dimensions: {width}x{height}",
                        code="INVALID_DIMENSIONS",
                        path=str(path),
                        details={'width': width, 'height': height}
                    )
                    validation_result.set_validated()
                    return validation_result
                validation_result.set_success(message=f"File successfully opened with RasterIO.", code="OPEN_PASSED")
                return validation_result
        except RasterioIOError as e:
            validation_result.set_failure(
                message=f"Failed to open file with RasterIO: {str(e)}",
                code="OPEN_FAILED",
                path=str(path),
                details={'error': str(e)}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not open raster file '{path}'.",
                code="OPEN_ERROR",
                path=str(path),
                details={"exception": str(exc)}
            )
            return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """
           Validate that the raster file has a valid Coordinate Reference System.

           Generic implementation using RasterIO that works for most raster formats.
           Subclasses can override this method for format-specific CRS handling.

           Avoids importing RasterIO at module import time to keep the package importable
           even when RasterIO is not installed.

           Checks:
           - CRS is present
           - CRS is valid and can be parsed
           - EPSG code is available (if applicable)
        """

        identifier = file_format.get_identifier()

        try:
            import rasterio
            from rasterio.errors import RasterioIOError
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
                crs = src.crs
                self.crs = crs
                # CRS needs to be present to be validated.
                if crs is None:
                    validation_result.set_uncertainty(
                        message=f"File has no CRS defined.",
                        code="CRS_MISSING",
                        path=str(path)
                    )
                    return validation_result

                return compare_crs(crs, file_format, path, validation_result)

        except RasterioIOError as e:
            validation_result.set_uncertainty(
                message=f"Failed to read CRS from file {identifier}: {str(e)}",
                code="CRS_FAILED",
                path=str(path),
                details={'error': str(e)}
            )
            return validation_result
        except Exception as e:
            validation_result.set_uncertainty(
                message=f"Unexpected error while validating CRS for file {identifier}: {str(e)}",
                code="CRS_ERROR",
                path=str(path),
                details={'error': str(e), 'error_type': type(e).__name__}
            )
            return validation_result
