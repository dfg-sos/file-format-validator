"""Also NetCDF-CF"""
from typing import List

from eo_format_validator.model import FileInput,Format,ValidationResult
from .raster_file_validator import RasterFileValidator
from ..registry import Registry
from eo_format_validator.util import compare_crs


@Registry.register("format_4115")
class NetCDFValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.cdf', '.nc4', '.nc']

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        """
           Validate that the NetCDF file can be opened and has valid basic structure.

           Avoids importing xarray at module import time to keep the package importable
           even when xarray is not installed.

           Checks:
              - File can be opened with xarray
              - File has at least one data variable
              - Dimensions are valid (> 0)
        """

        try:
            import xarray as xr
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"The NetCDFValidator requires the 'xarray' library to be installed.",
                code="XARRAY_MISSING",
                details={"exception": str(exc)}
            )
            return validation_result

        path = file_input.get_path()

        try:
            with xr.open_dataset(path) as ds:

                # check if dataset has data variables
                if len(ds.data_vars) == 0:
                    validation_result.set_failure(
                        message=f"NetCDF file has no data variables.",
                        code="NO_DATA_VARS",
                        path=str(path)
                    )
                    validation_result.set_validated()
                    return validation_result

                # check dimensions
                for dim_name, dim_size in ds.dims.items():
                    if dim_size <= 0:
                        validation_result.set_failure(
                            message=f"Invalid dimension '{dim_name}': size {dim_size}",
                            code="INVALID_DIMENSION",
                            path=str(path),
                            details={'dimension': dim_name, 'size': dim_size}
                        )
                        validation_result.set_validated()
                        return validation_result

                # file successfully opened
                validation_result.set_success(
                    message=f"NetCDF file successfully opened with xarray.",
                    code="OPEN_PASSED"
                )
                return validation_result

        except (OSError, IOError) as e:
            validation_result.set_failure(
                message=f"Failed to open NetCDF file: {str(e)}",
                code="OPEN_FAILED",
                path=str(path),
                details={'error': str(e)}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not open NetCDF file '{path}'.",
                code="OPEN_ERROR",
                path=str(path),
                details={"exception": str(exc), "exception_type": type(exc).__name__}
            )
            return validation_result


    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """
           Validate that the NetCDF file has a valid Coordinate Reference System.

           Avoids importing xarray at module import time to keep the package
           importable even when these libraries are not installed.

           Checks:
              - CRS is present
              - CRS can be parsed to EPSG code
              - EPSG code matches expected (if specified)
        """

        try:
            import xarray as xr
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"The NetCDFValidator requires the 'xarray' library to be installed.",
                code="XARRAY_MISSING",
                details={"exception": str(exc)}
            )
            return validation_result

        path = file_input.get_path()

        try:
            with xr.open_dataset(path) as ds:

                # compare CRS with expected
                return compare_crs(ds.rio.crs, file_format, path, validation_result)

        except (OSError, IOError) as e:
            validation_result.set_uncertainty(
                message=f"Failed to read CRS from NetCDF file: {str(e)}",
                code="CRS_FAILED",
                path=str(path),
                details={'error': str(e)}
            )
            return validation_result
        except Exception as e:
            validation_result.set_uncertainty(
                message=f"Unexpected error while validating CRS for NetCDF file: {str(e)}",
                code="CRS_ERROR",
                path=str(path),
                details={'error': str(e), 'error_type': type(e).__name__}
            )
            return validation_result

#----------------------optional further advanced checks-----------------------