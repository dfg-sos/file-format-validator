"""Specification: http://docs.opengeospatial.org/is/12-007r2/12-007r2.html
   Developer documentation: https://developers.google.com/kml/documentation/kmlreference"""
from typing import List, Optional, Set
import xml.etree.ElementTree as ET
import re
from pyproj import CRS

from ..model import ValidationRequest, ValidationResult,Error,Cause,Warning,Cause,Info
from .eo_file_format_validator import EOValidationRequest
from .vector_file_validator import VectorFileValidator
from ..registry import Registry


@Registry.register("format_4114")
class KMLValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.kml', '.kmz']  # .kmz for zip

    def assert_can_open(self, request:ValidationRequest) -> ValidationResult:
        """Short open/parse check using ElementTree. Reports OPEN_OK or errors.
           Only ensures the file exists and is valid XML/KML. Does not perform deep
           structural validation.
        """
        try:
            # quick parse (will raise ParseError on invalid XML)
            tree = ET.parse(str(request.actual_file.path))
            root = tree.getroot()
        except ET.ParseError as exc:
            return ValidationResult.failure(
                request,
                Error(message=f"KML XML parse error: {exc}", cause=Cause.STRUCTURAL_MALFORMED)
            )
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Could not open/parse KML file: {exc}", cause=Cause.UNKNOWN)           
        )
        tag = root.tag
        tag_name = tag.split('}', 1)[-1] if '}' in tag else tag
        if tag_name.lower() != 'kml':
            # not strictly an error — some KMLs may omit the outer <kml> namespace
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Root element does not appear to be <kml> — file parsed as XML but may not be strict KML. Root tag: {tag_name}", cause=Cause.STRUCTURAL_MALFORMED),
            )
        return ValidationResult.success(request)

    def get_crs(self, request: EOValidationRequest) -> Optional[CRS]:
        """Return the first CRS-like value found in the KML, if any."""
        try:
            tree = ET.parse(str(request.actual_file.path))
            root = tree.getroot()
        except Exception:
            return None

        re_epsg = re.compile(r"epsg\s*[:=]?\s*(\d{3,7})", flags=re.IGNORECASE)
        re_urn = re.compile(r"urn:ogc:def:crs:EPSG::(\d{3,7})", flags=re.IGNORECASE)

        def extract_candidate(value: str) -> Optional[str]:
            if not value:
                return None
            value = value.strip()

            m = re_urn.search(value) or re_epsg.search(value)
            if m:
                return m.group(1)

            if value.lower().startswith("epsg:"):
                return value

            return value

        candidate = None

        for elem in root.iter():
            for k, v in elem.attrib.items():
                if not v:
                    continue

                k_lower = k.lower()
                if "srs" in k_lower or "crs" in k_lower or "epsg" in k_lower:
                    candidate = extract_candidate(v)
                    if candidate:
                        break

                if re_urn.search(v) or re_epsg.search(v):
                    candidate = extract_candidate(v)
                    if candidate:
                        break

            if candidate:
                break

            if elem.text and ("srs" in (elem.tag.lower()) or "crs" in (elem.tag.lower())):
                candidate = extract_candidate(elem.text)
                if candidate:
                    break

        if not candidate:
            return None

        try:
            return CRS.from_user_input(candidate)
        except Exception:
            return None


    def assert_geometry_type(self, request: EOValidationRequest) -> ValidationResult:
        """Detect KML geometry and compare it to the expected geometry type."""
        try:
            tree = ET.parse(str(request.actual_file.path))
            root = tree.getroot()
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Could not parse KML for shape detection:\n{exc}", cause=Cause.STRUCTURAL_MALFORMED),
            )

        def strip_tag(tag: str) -> str:
            return tag.split("}", 1)[-1] if "}" in tag else tag

        def normalize_expected(expected: str) -> str:
            exp = str(expected).strip().lower()
            if exp in ("point", "points", "multipoint"):
                return "POINT"
            if exp in ("line", "linestring", "multilinestring"):
                return "LINESTRING"
            if exp in ("polygon", "multipolygon"):
                return "POLYGON"
            if exp in ("mixed", "geometrycollection", "geometry collection"):
                return "GEOMETRYCOLLECTION"
            return exp.upper()

        def family(wkt_type: str) -> str:
            wkt_type = wkt_type.upper()
            if wkt_type.startswith("MULTI"):
                return wkt_type[5:]
            return wkt_type

        def detect_wkt_type() -> Optional[str]:
            counts = {"POINT": 0, "LINESTRING": 0, "POLYGON": 0}
            max_placemarks = 200
            placemark_count = 0

            for elem in root.iter():
                if strip_tag(elem.tag).lower() != "placemark":
                    continue

                placemark_count += 1
                for sub in elem.iter():
                    tag = strip_tag(sub.tag).lower()
                    if tag == "point":
                        counts["POINT"] += 1
                    elif tag == "linestring":
                        counts["LINESTRING"] += 1
                    elif tag == "polygon":
                        counts["POLYGON"] += 1

                if placemark_count >= max_placemarks:
                    break

            present = [name for name, count in counts.items() if count > 0]
            if not present:
                return None

            if len(present) > 1:
                return "GEOMETRYCOLLECTION"

            single = present[0]
            if counts[single] > 1:
                return f"MULTI{single}"

            return single

        detected_wkt = detect_wkt_type()
        if not detected_wkt:
            return ValidationResult.uncertain(
                request,
                Warning(message="No geometries detected in sampled Placemarks.", cause=Cause.MISSING_METADATA),
            )

        expected = request.geometry_type if request.geometry_type else None
        if not expected:
            return ValidationResult.success(
                request,
                Info(message="No expected geometry type given, skipping geometry type validation."),
            )

        if family(detected_wkt) == family(str(expected)):
            return ValidationResult.success(request)

        return ValidationResult.failure(
            request,
            Error(
                message=f"Detected WKT geometry '{detected_wkt}' does not match expected '{expected}'.",
                cause=Cause.METADATA_MISMATCH,
            ),
        )
        