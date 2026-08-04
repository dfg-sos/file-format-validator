"""Specification: http://docs.opengeospatial.org/is/12-007r2/12-007r2.html
   Developer documentation: https://developers.google.com/kml/documentation/kmlreference"""
from typing import List, Optional, Set
import xml.etree.ElementTree as ET
import re
from pyproj import CRS
from shapely import GeometryType

from ...model import ValidationRequest, ValidationResult,Error,Cause,Warning,Cause,Info
from .eo_file_format_validator import EOValidationRequest
from .vector_file_validator import VectorFileValidator
from ...registry import registry


@registry.register("format_4114")
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
        """Return EPSG:4326 if the file is a valid KML document."""
        try:
            tree = ET.parse(str(request.actual_file.path))
            root = tree.getroot()
            
            # Verify it's a KML file (handling optional XML namespaces)
            if root.tag.endswith('kml'):
                return CRS.from_epsg(4326)
                
        except Exception:
            # Returns None if file is corrupted, unreadable, or not XML
            return None
            
        return None

    def get_geometry_types(self, request: EOValidationRequest) -> List[GeometryType]:
        """Get all geometry types found in the KML file.
        
        Parses KML file and samples up to 200 Placemarks to detect geometry types.
        
        Args:
            request: The validation request containing the file to analyze
            
        Returns:
            List of GeometryType enum values found in the file
        """
        types = set()
        try:
            tree = ET.parse(str(request.actual_file.path))
            root = tree.getroot()
        except Exception:
            return list(types)

        def strip_tag(tag: str) -> str:
            return tag.split("}", 1)[-1] if "}" in tag else tag

        def detect_geometry_type() -> Optional[str]:
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
                # Multiple geometry types found
                for name in present:
                    try:
                        types.add(GeometryType[name])
                    except (KeyError, AttributeError):
                        pass
                return "GEOMETRYCOLLECTION"

            single = present[0]
            if counts[single] > 1:
                # Multiple geometries of same type
                try:
                    types.add(GeometryType[f"MULTI{single}"])
                except (KeyError, AttributeError):
                    try:
                        types.add(GeometryType[single])
                    except (KeyError, AttributeError):
                        pass
            else:
                # Single geometry
                try:
                    types.add(GeometryType[single])
                except (KeyError, AttributeError):
                    pass

            return single

        detect_geometry_type()
        return list(types)
        