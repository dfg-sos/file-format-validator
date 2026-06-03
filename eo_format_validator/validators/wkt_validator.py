"""Well-known textual representation of geometry"""
from typing import List
from pyproj import CRS
from shapely import wkt

from eo_format_validator.model import ValidationResult,Format,FileInput
from eo_format_validator.util import compare_crs,compare_shape_type, normalize_geometry_to_shape_type
from ..registry import Registry
from .vector_file_validator import VectorFileValidator

@Registry.register("format_4122")
class WKTValidator(VectorFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.wkt', '.txt']




    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        path = file_input.get_path()
        try:
            text = path.read_text(encoding="utf-8").strip()

            # remove GeoSPARQL / RDF WKT prefix
            if text.startswith("<"):
                text = text.split(">", 1)[1].strip()

            # remove EWKT prefix
            if text.upper().startswith("SRID="):
                text = text.split(";", 1)[1]

            geom = wkt.loads(text)
            validation_result.set_success(
                message="WKT parsed successfully.",
                code="OPEN_OK",
                details={"geom_type": geom.geom_type}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_failure(
                message="Invalid WKT geometry.",
                code="OPEN_FAILED",
                path=str(path),
                details={"exception": str(exc)}
            )
            return validation_result

    def assert_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        path = file_input.get_path()
        try:
            text = path.read_text(encoding="utf-8").strip()

            if text.startswith("<"):
                text = text.split(">", 1)[1].strip()

            if text.upper().startswith("SRID="):
                epsg = int(text.split(";", 1)[0].split("=")[1])
            else:
                crs = CRS.from_wkt(text)
                epsg = crs.to_epsg()
            if not epsg:
                validation_result.set_uncertainty(
                    message="CRS found but no EPSG code available.",
                    code="CRS_NO_EPSG",
                    path=str(path)
                )
                return validation_result

            return compare_crs(epsg, file_format, path, validation_result)
        except Exception as exc:
            validation_result.set_uncertainty(
                message="Could not determine CRS from WKT.",
                code="CRS_PARSE_FAILED",
                path=str(path),
                details={"exception": str(exc)}
            )
            return validation_result

    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        path = file_input.get_path()
        try:
            text = path.read_text(encoding="utf-8").strip()

            # remove GeoSPARQL / RDF WKT prefix
            if text.startswith("<"):
                text = text.split(">", 1)[1].strip()

            # remove EWKT prefix
            if text.upper().startswith("SRID="):
                text = text.split(";", 1)[1]

            geom = wkt.loads(text)
            detected = geom.geom_type.lower()
            return compare_shape_type(file_format.get_shape_type(), normalize_geometry_to_shape_type(detected), validation_result)
        except Exception as exc:
            validation_result.set_uncertainty(
                message="Could not parse WKT geometry.",
                code="GEOM_PARSE_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result
