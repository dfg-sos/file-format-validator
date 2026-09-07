"""GPX (GPS Exchange Format), Sepcification: V1.1 https://www.topografix.com/GPX/1/1/gpx-strict.xsd,
                                             V1.0 https://www.topografix.com/GPX/1/0/gpx-strict.xsd"""
from typing import List, Tuple, Optional, Set
import xml.etree.ElementTree as ET
import fiona
from shapely import GeometryType

from format_validator.model import ValidationRequest, ValidationResult,Error,Cause,Warning,FormatIdentifier
from .vector_file_validator import VectorFileValidator
from ...registry import registry


GPX_NAMESPACES = {
        'http://www.topografix.com/GPX/1/0',  # GPX 1.0
        'http://www.topografix.com/GPX/1/1',  # GPX 1.1
    }

# the required root element name that identifies a GPX document
GPX_ROOT_ELEMENT = 'gpx'

@registry.register(FormatIdentifier.GPX)
class GPXValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.gpx']

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        """Validate that the file is valid GPX per specification."""

        # parse XML
        try:
            tree = ET.parse(str(request.actual_file.path))
            root = tree.getroot()
        except ET.ParseError as exc:
            return ValidationResult.failure(
                request,
                Error(message=f"GPX parse error: {exc}", cause=Cause.STRUCTURAL_MALFORMED)
            )
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Could not open/parse gpx file: {exc}", cause=Cause.UNKNOWN)
            )

        # check if GPX according to specification
        is_gpx, error_details = self._is_gpx_document(root)

        if not is_gpx:
            return ValidationResult.failure(
                request,
                Error(message="XML file does not conform to GPX specification.", cause=Cause.STRUCTURAL_MALFORMED)
            )
        try:
            with fiona.open(str(request.actual_file.path), driver='GPX') as src:
                _ = src.schema
                _ = src.crs
        except Exception as e:
            return ValidationResult.failure(
                request,
                Error(message=f"File has GPX structure but Fiona cannot read it: {e}", cause=Cause.FILE_OPEN_ERROR)
            )

        return ValidationResult.success(request)

    def _is_gpx_document(self, root: ET.Element) -> Tuple[bool, dict]:
        """Check if XML has root element in GPX namespace as defined in specification to differentiate from other XML files. GPX is identified by its namespace and root.
           To allow further GPX-based files, e.g. platform-specific extensions like Garmin, allow for additional namespaces to be present further below in the document.

        Check if the XML root element conforms to GPX specification.

        Per GPX specification:
        - Root element MUST be 'gpx'
        - Root element MUST be in a GPX namespace

        Args:
            root: The XML root element

        Returns:
            Tuple of (is_gpx: bool, details: dict)
        """
        details = {}

        # extract namespace and local name from root element
        namespace, local_name = self._split_tag(root.tag)

        details['root_element'] = local_name
        details['namespace'] = namespace or "none"

        # check 1: Root element must be 'gpx'
        if local_name != GPX_ROOT_ELEMENT:
            details['error'] = f"Root element is '{local_name}', expected '{GPX_ROOT_ELEMENT}'"
            return False, details

        # check 2: Root element must be in GPX namespace
        if not namespace or namespace not in GPX_NAMESPACES:
            details['error'] = f"Root element namespace is '{namespace}', expected one of: {list(GPX_NAMESPACES)}"
            return False, details

        # checks passed
        return True, details

    def _split_tag(self, tag: str) -> Tuple[Optional[str], str]:
        """Split a qualified XML tag into (namespace, local_name).

        Args:
            tag: XML tag, either 'localname' or '{namespace}localname'

        Returns:
            Tuple of (namespace or None, local_name)
        """
        if '}' in tag:
            namespace, local_name = tag.split('}')
            namespace = namespace[1:]  # Remove leading '{'
            return namespace, local_name
        return None, tag

    def get_geometry_types(self, request: ValidationRequest) -> List[GeometryType]:
        """Get all geometry types found in the GPX file.
        
        Parses GPX file and detects geometry types based on feature types:
        - wpt (waypoints) → Point
        - rte (routes) with route points → LineString
        - trk (tracks) with track segments → LineString
        
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

        max_features_to_inspect = 50
        waypoint_count = 0
        route_count = 0
        track_count = 0

        for elem in root.iter():
            tag = strip_tag(elem.tag)
            
            # Check for waypoints (wpt) - represent Point geometry
            if tag.lower() == "wpt" and waypoint_count < max_features_to_inspect:
                waypoint_count += 1
                types.add(GeometryType.POINT)
                
            # Check for routes (rte) - represent LineString geometry
            elif tag.lower() == "rte" and route_count < max_features_to_inspect:
                route_count += 1
                # Check if route has at least 2 route points to form a line
                rtept_count = 0
                for child in elem.iter():
                    if strip_tag(child.tag).lower() == "rtept":
                        rtept_count += 1
                        if rtept_count >= 2:
                            break
                if rtept_count >= 2:
                    types.add(GeometryType.LINESTRING)
                    
            # Check for tracks (trk) - represent LineString geometry
            elif tag.lower() == "trk" and track_count < max_features_to_inspect:
                track_count += 1
                # Check if track has at least one segment with 2 track points to form a line
                for trkseg in elem.iter():
                    if strip_tag(trkseg.tag).lower() == "trkseg":
                        trkpt_count = 0
                        for child in trkseg.iter():
                            if strip_tag(child.tag).lower() == "trkpt":
                                trkpt_count += 1
                                if trkpt_count >= 2:
                                    break
                        if trkpt_count >= 2:
                            types.add(GeometryType.LINESTRING)
                            break

        return list(types)
