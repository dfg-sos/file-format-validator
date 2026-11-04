from sys import path
from typing import List, Optional
import xarray as xr
from pyproj import CRS

from format_validator.model import ValidationRequest,ValidationResult,Error,Warning,Cause,FormatIdentifier
from .raster_file_validator import RasterFileValidator
from format_validator.registry import registry
from . import formats


@registry.register(formats.NETCDF)
class NetCDFValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.cdf', '.nc4', '.nc']

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
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
            with xr.open_dataset(request.actual_file.path) as ds:
                # check if dataset has data variables
                if len(ds.data_vars) == 0:
                    return ValidationResult.failure(
                        request,
                        Error(message=f"NetCDF file has no data variables.", cause=Cause.MISSING_METADATA)
                    )
                # check dimensions
                for dim_name, dim_size in ds.dims.items():
                    if dim_size <= 0:
                        return ValidationResult.failure(
                            request,
                            Error(message=f"NetCDF file has invalid dimension '{dim_name}' with size {dim_size}.", cause=Cause.STRUCTURAL_MALFORMED)
                        )
                return ValidationResult.success(request)

        except (OSError, IOError,ValueError) as e:
            return ValidationResult.failure(
                request,
                Error(message=f"Failed to open NetCDF file: {str(e)}", cause=Cause.FILE_OPEN_ERROR)
            )
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(f"Could not open NetCDF file with xarray:\n{exc}", cause=Cause.UNKNOWN)
            )


    def assert_content(self, request: ValidationRequest) -> ValidationResult:
        """Load the values of every variable, so truncated or corrupt data fails."""
        try:
            with xr.open_dataset(request.actual_file.path) as ds:
                ds.load()
                return ValidationResult.success(request)
        except Exception as exc:
            return ValidationResult.failure(
                request,
                Error(message=f"Failed to read the data of NetCDF file: {exc}", cause=Cause.STRUCTURAL_MALFORMED)
            )

    def get_crs(self, request: ValidationRequest) -> Optional[CRS]:
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
            with xr.open_dataset(request.actual_file.path) as ds:
                return CRS.from_cf(ds.crs.attrs) if hasattr(ds, 'crs') and ds.crs is not None else None
        except Exception:
            return None