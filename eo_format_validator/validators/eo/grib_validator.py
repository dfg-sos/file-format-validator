from typing import List,Optional
import xarray as xr
from pyproj import CRS

from .eo_file_format_validator import EOValidationRequest
from ...model import ValidationRequest,ValidationResult,Error,Cause
from .raster_file_validator import RasterFileValidator
from ...registry import registry


@registry.register("format_4113")
class GRIBValidator(RasterFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.grib', '.grib1', '.grb', '.gb', '.grib2', '.grb2'] # commonly used file extensions, no officially specified one

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        try:
            ds = xr.open_dataset(str(request.actual_file.path), engine="cfgrib")
            ds.close()
            return ValidationResult.success(request)
        except Exception as exc:
            return ValidationResult.failure(
                request,
                Error(message=f"Could not open GRIB file with cfgrib (xarray):\n{exc}", cause=Cause.FILE_OPEN_ERROR)
            )

    def get_crs(self, request: EOValidationRequest) -> Optional[CRS]:
        """
        If xarray/cfgrib can open the file, infer CRS as EPSG from shapeOfTheEarth parameter. Extend mapping for further codes.
        """
        try:
            ds = xr.open_dataset(
                request.actual_file.path, 
                engine="cfgrib",
                backend_kwargs={'read_keys': ['projString']}
            )
            first_var = ds[list(ds.keys())[0]]
            if getattr(first_var, "GRIB_gridType", None) == "regular_ll":
                return CRS.from_epsg(4326)
            return None
        except Exception as exc:
            return None
