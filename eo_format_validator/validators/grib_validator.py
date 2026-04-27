from pathlib import Path
from typing import List

from eo_format_validator.validators.raster_file_validator import RasterFileValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.validator_registry import validators
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.crs_operations import compare_crs


@validators.register("format_4113")
class GRIBValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.grib', '.grib1', '.grb', '.gb', '.grib2', '.grb2'] # commonly used file extensions, no officially specified one

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        """Quick open check: try cfgrib (xarray)."""
        path: Path = file_input.get_path()

        # try cfgrib via xarray
        try:
            import xarray as xr
            # xr.open_dataset with engine='cfgrib' reads GRIB metadata (requires cfgrib/ecCodes)
            ds = xr.open_dataset(str(path), engine="cfgrib")
            # gather some light metadata
            vars_count = len(ds.data_vars) if hasattr(ds, 'data_vars') else None
            coords = list(ds.coords.keys()) if hasattr(ds, 'coords') else []
            ds.close()

            validation_result.set_success(
                message="GRIB successfully opened via xarray/cfgrib.",
                code="OPEN_OK_CFGRIB",
                details={"variables": vars_count, "coords": coords}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_failure(
                message="Could not open GRIB file with cfgrib (xarray).",
                code="OPEN_FAILED",
                details={"cfgrib_error": str(exc)}
            )
            return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """Quick CRS detection for GRIB files.
           Strategy:
              - If xarray/cfgrib can open the file, infer CRS as EPSG from shapeOfTheEarth parameter. Extend mapping for further codes.
        """
        path: Path = file_input.get_path()

        # prefer cfgrib/xarray
        candidate = None
        try:
            import xarray as xr
            #ds = xr.open_dataset(str(path), engine="cfgrib")
            #coords = set(ds.coords.keys()) if hasattr(ds, 'coords') else set()
            #attrs = getattr(ds, 'attrs', {}) or {}
            #ds.close()



            ds = xr.open_dataset(str(path), engine="cfgrib",
                                 backend_kwargs={'read_keys': ['shapeOfTheEarth']})

            epsg = None
            match ds[list(ds.keys())[0]].GRIB_shapeOfTheEarth:
                case 4:
                    epsg = 42310
                case 5:
                    epsg = 4326
                case 9:
                    epsg = 4277
            return compare_crs(epsg, file_format, path, validation_result)
            # typical cfgrib coords: latitude/longitude for regular grids
            #if any(c.lower() in ('latitude', 'lat') for c in coords) and any(c.lower() in ('longitude', 'lon', 'long') for c in coords):
            #    candidate = 'EPSG:4326'
            # rotated pole detection (cfgrib may expose a coord or attribute)
            #if not candidate and any('rotated' in c.lower() for c in coords) or any('rotated' in str(v).lower() for v in attrs.values()):
            #    candidate = 'rotated_latitude_longitude'
        except Exception as exc:
            validation_result.set_uncertainty(
                message="Could not open GRIB file with cfgrib (xarray).",
                code="OPEN_FAILED",
                details={"cfgrib_error": str(exc)}
            )
            return validation_result
