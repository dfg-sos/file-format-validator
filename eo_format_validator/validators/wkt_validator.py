"""Well-known textual representation of geometry"""
from typing import List,Optional
from pyproj import CRS
from shapely import wkt

from ..model import ValidationResult,ValidationRequest,Error,Cause,Warning
from ..registry import Registry
from .vector_file_validator import VectorFileValidator
from .eo_file_format_validator import EOValidationRequest

@Registry.register("format_4122")
class WKTValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.wkt', '.txt']




    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        path = request.actual_file.path
        try:
            text = path.read_text(encoding="utf-8").strip()

            # remove GeoSPARQL / RDF WKT prefix
            if text.startswith("<"):
                text = text.split(">", 1)[1].strip()

            # remove EWKT prefix
            if text.upper().startswith("SRID="):
                text = text.split(";", 1)[1]

            geom = wkt.loads(text)
            return ValidationResult.success(request)
        except Exception as exc:
            return ValidationResult.failure(
                request,
                Error(message="Invalid WKT geometry.", cause=Cause.STRUCTURAL_MALFORMED)
            )

    def get_crs(self, request: EOValidationRequest) -> Optional[CRS]:
        try:
            text = request.actual_file.path.read_text(encoding="utf-8").strip()

            if text.startswith("<"):
                text = text.split(">", 1)[1].strip()

            if text.upper().startswith("SRID="):
                epsg = int(text.split(";", 1)[0].split("=")[1])
            else:
                return CRS.from_wkt(text)
        except Exception:
            return None

    def assert_geometry_type(self, request: EOValidationRequest) -> ValidationResult:
        path = request.actual_file.path
        if not request.geometry_type:
            return ValidationResult.uncertain(
                request,
                Warning("No expected geometry type provided for WKT file, skipping geometry type check.", cause=Cause.MISSING_METADATA)
            )
        try:
            text = path.read_text(encoding="utf-8").strip()

            # remove GeoSPARQL / RDF WKT prefix
            if text.startswith("<"):
                text = text.split(">", 1)[1].strip()

            # remove EWKT prefix
            if text.upper().startswith("SRID="):
                text = text.split(";", 1)[1]

            geom = wkt.loads(text)
            detected = geom.geom_type
            expected = request.geometry_type 
            if detected != expected:
                return ValidationResult.failure(
                    request,
                    Error(message=f"Geometry type mismatch: detected '{detected}' vs expected '{expected}'.", cause=Cause.METADATA_MISMATCH)
                )
            return ValidationResult.success(request)
           
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(f"Could not detect geometry type from WKT file:\n{str(exc)}",cause=Cause.MISSING_METADATA)
            )
