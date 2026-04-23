from pathlib import Path
from typing import List

from eo_format_validator.api.raster_file_validator import RasterFileValidator
from eo_format_validator.core.file_input import FileInput
from eo_format_validator.core.format import Format
from eo_format_validator.core.validator_registry import validators
from eo_format_validator.result.validation_result import ValidationResult


@validators.register("format_4109")
class GeoTIFFValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']


    #----------------------optional further advanced checks-----------------------
    def _additional_checks (self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        """Additional checks for a valid GeoTIFF file. Can be included in STRICT ValidationMode when overriding method."""
        tags = check_tiff_tags(str(file_input.get_path()))
        if not tags:
            validation_result.set_failure(
                message=f"No GeoTIFF tags found.",
                code="NO_TAGS"
            )

        path = file_input.get_path()

        from rasterio.errors import RasterioIOError
        try:
            import rasterio
            with rasterio.open(path) as src:
                width = src.width
                height = src.height
                count = src.count
                dtype = src.dtypes[0] if src.dtypes else None
                profile = src.profile
                driver = profile.get("driver") if profile is not None else getattr(src, "driver", None)

                # driver check (GTiff is the common rasterio driver for GeoTIFF)
                if driver and str(driver).lower() != "gtiff":
                    validation_result.set_failure(
                        message=f"Opened file but driver '{driver}' is not 'GTiff'.",
                        code="DRIVER_MISMATCH",
                        details={"driver": driver}
                    )

                # validate dimensions
                if width <= 0 or height <= 0:
                    validation_result.set_failure(
                        message=f"Invalid raster dimensions: {width}x{height}",
                        code="INVALID_DIMENSIONS",
                        path=str(path),
                        details={'width': width, 'height': height}
                    )
                    return validation_result

                # validate band count
                if count <= 0:
                    validation_result.set_failure(
                        message=f"Invalid band count: {count}",
                        code="INVALID_BAND_COUNT",
                        path=str(path),
                        details={'band_count': count}
                    )
                    return validation_result

                validation_result.set_success(
                    message=f"GeoTIFF successfully opened: {width}x{height} pixels, {count} band(s)",
                    code="OPEN_PASSED",
                    details={
                        'dimensions': f"{width}x{height}",
                        'bands': count,
                        'dtype': str(dtype)
                    }
                )
        except RasterioIOError as e:
            validation_result.set_failure(
                message=f"Failed to open GeoTIFF file with RasterIO: {str(e)}",
                code="OPEN_FAILED",
                path=str(path),
                details={'error': str(e)}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not open GeoTIFF file '{path}'.",
                code="OPEN_ERROR",
                path=str(path),
                details={"exception": str(exc)}
            )
        return validation_result

GEO_TAG_IDS = {33550: "ModelPixelScaleTag",
               33922: "ModelTiepointTag",
               34735: "GeoKeyDirectoryTag",
               34736: "GeoDoubleParamsTag",
               34737: "GeoAsciiParamsTag"}

def check_tiff_tags(path):
    tags_found = {}
    try:
        from tifffile import TiffFile
        with TiffFile(path) as tif:
            page = tif.pages[0]
            for tag in page.tags.values():
                if tag.code in GEO_TAG_IDS:
                    tags_found[tag.code] = GEO_TAG_IDS[tag.code]
    except Exception as e:
        return {"error": f"tifffile error: {e}"}
    return tags_found

