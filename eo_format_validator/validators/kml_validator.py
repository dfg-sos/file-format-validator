"""Specification: http://docs.opengeospatial.org/is/12-007r2/12-007r2.html
   Developer documentation: https://developers.google.com/kml/documentation/kmlreference"""
from pathlib import Path
from typing import List, Set



import xml.etree.ElementTree as ET

from eo_format_validator.model import FileInput, Format, ValidationResult
from eo_format_validator.util import compare_crs
from .vector_file_validator import VectorFileValidator
from ..registry import Registry


@Registry.register("format_4114")
class KMLValidator(VectorFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.kml', '.kmz']  # .kmz for zip

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        """Short open/parse check using ElementTree. Reports OPEN_OK or errors.
           Only ensures the file exists and is valid XML/KML. Does not perform deep
           structural validation.
        """
        path: Path = file_input.get_path()

        try:
            # quick parse (will raise ParseError on invalid XML)
            tree = ET.parse(str(path))
            root = tree.getroot()
        except ET.ParseError as exc:
            validation_result.set_failure(
                message=f"KML XML parse error: {exc}",
                code="OPEN_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not open/parse KML file: {exc}",
                code="OPEN_ERROR",
                details={"exception": str(exc)}
            )
            return validation_result

        # basic sanity: check for KML tag or common namespace
        tag = root.tag
        tag_name = tag.split('}', 1)[-1] if '}' in tag else tag
        if tag_name.lower() != 'kml':
            # not strictly an error — some KMLs may omit the outer <kml> namespace
            validation_result.add_warning(
                message="Root element does not appear to be <kml> — file parsed as XML but may not be strict KML.",
                code="NOT_STRICT_KML",
                details={"root_tag": tag}
            )

        validation_result.set_success(
            message="KML file parsed successfully.",
            code="OPEN_OK"
        )
        return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """KML is by specification WGS84/EPSG:4326. This method attempts to check whether this is true.
           Find first plausible CRS in KML.
              - Parse XML and look for attributes/values mentioning 'srs', 'srsName', 'crs', or 'EPSG'.
        """
        import re

        path: Path = file_input.get_path()

        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not parse KML XML for CRS detection: {exc}",
                code="XML_PARSE_ERROR",
                details={"exception": str(exc)}
            )
            return validation_result

        # quick scan for attributes or text containing EPSG or URN
        re_epsg = re.compile(r"epsg\s*[:=]?\s*(\d{3,7})", flags=re.IGNORECASE)
        re_urn = re.compile(r"urn:ogc:def:crs:EPSG::(\d{3,7})", flags=re.IGNORECASE)

        candidate = None
        for elem in root.iter():
            # attributes
            for k, v in elem.attrib.items():
                if not v:
                    continue
                kval = k.lower()
                if 'srs' in kval or 'crs' in kval or 'epsg' in kval:
                    # normalize if possible
                    m = re_urn.search(v) or re_epsg.search(v)
                    if m:
                        candidate = f"EPSG:{m.group(1)}"
                    else:
                        candidate = v.strip()
                    break
                # value may contain an EPSG/URN
                if re_urn.search(v) or re_epsg.search(v):
                    m = re_urn.search(v) or re_epsg.search(v)
                    candidate = f"EPSG:{m.group(1)}"
                    break
            if candidate:
                break

        return compare_crs(candidate, file_format, path, validation_result)


    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        """Short shape type check for KML: detect predominant geometry and compare to expected.

                - Parse KML and scan a limited number of Placemarks for Point/LineString/Polygon.
                - Determine a single detected category (or 'mixed' if multiple).
                - If the Format provides a shape type, compare and return SHAPE_MATCH or SHAPE_MISMATCH.
                """
        path: Path = file_input.get_path()

        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not parse KML for shape detection: {exc}",
                code="SHAPE_PARSE_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result

        def strip_tag(tag: str) -> str:
            return tag.split('}', 1)[-1] if '}' in tag else tag

        found: Set[str] = set()
        max_placemarks = 200
        count = 0

        for elem in root.iter():
            if strip_tag(elem.tag).lower() == 'placemark':
                count += 1
                for child in elem:
                    c = strip_tag(child.tag).lower()
                    if c == 'point':
                        found.add('point')
                    elif c == 'linestring':
                        found.add('line')
                    elif c == 'polygon':
                        found.add('polygon')
                    elif c == 'multigeometry':
                        for sub in child.iter():
                            sc = strip_tag(sub.tag).lower()
                            if sc == 'point':
                                found.add('point')
                            elif sc == 'linestring':
                                found.add('line')
                            elif sc == 'polygon':
                                found.add('polygon')
                if count >= max_placemarks:
                    break

        if not found:
            validation_result.set_uncertainty(
                message="No geometries detected in sampled Placemarks.",
                code="NO_GEOMETRIES"
            )
            return validation_result

        # choose a single detected category: if multiple -> 'mixed', else the one
        detected = 'geometrycollection' if len(found) > 1 else next(iter(found))

        # get expected from Format if available
        expected = file_format.get_shape_type()
        if expected:
            exp_norm = str(expected).strip().lower()
            # normalize some synonyms
            if exp_norm in ('points', 'point', 'multipoint'):
                exp_norm = 'point'
            elif exp_norm in ('linestring', 'line', 'multilinestring'):
                exp_norm = 'line'
            elif exp_norm in ('polygon', 'multipolygon'):
                exp_norm = 'polygon'
            elif exp_norm in ('mixed',):
                exp_norm = 'mixed'

            if exp_norm == detected or (exp_norm == 'mixed' and detected == 'mixed'):
                validation_result.set_success(
                    message=f"Detected shape type matches expected: {exp_norm}",
                    code="SHAPE_MATCH",
                    details={"detected": detected, "expected": exp_norm}
                )
                return validation_result
            else:
                validation_result.set_failure(
                    message=f"Detected shape type '{detected}' does not match expected '{exp_norm}'.",
                    code="SHAPE_MISMATCH",
                    details={"detected": detected, "expected": exp_norm}
                )
                return validation_result

        # no expected provided -> just report detected
        validation_result.add_info(
            message="Detected geometry category in KML.",
            code="GEOM_DETECTED",
            details={"detected": detected}
        )
        return validation_result


##----------new------------
#"""Keyhole Markup Language (KML) validator.
#
#KML Specification:
#- OGC 07-147r2 (KML 2.2): https://www.ogc.org/standards/kml/
#- OGC 12-007r2 (KML 2.3): https://docs.ogc.org/is/12-007r2/12-007r2.html
#Official Schema: http://schemas.opengis.net/kml/
#
#Per OGC KML specification and Abstract Test Suite (OGC 14-068r2, ATC-101):
#- A KML document MUST have <kml> as the root element
#- The root element MUST be in one of the KML namespaces:
#  * KML 2.2: http://www.opengis.net/kml/2.2
#  * KML 2.3: http://www.opengis.net/kml/2.3
#
#Note: KML 2.3 maintains backward compatibility with 2.2, so both namespaces are valid.
#The namespace http://www.opengis.net/kml/2.2 is also used for KML 2.3 documents
#for compatibility reasons.
#"""
#from pathlib import Path
#from typing import List, Optional, Tuple
#import xml.etree.ElementTree as ET
#
#from eo_validator.api.vector_file_validator import VectorFileValidator
#from eo_validator.core.file_input import FileInput
#from eo_validator.core.format import Format
#from eo_validator.core.validator_registry import validators
#from eo_validator.result.validation_result import ValidationResult
#from eo_validator.utils.shape_operations import validate_shape_type_with_fiona
#
## Official KML namespaces per OGC specification
#KML_NAMESPACES = {
#    'http://www.opengis.net/kml/2.2',  # KML 2.2 (also used for KML 2.3)
#    'http://www.opengis.net/kml/2.3',  # KML 2.3
#    'http://earth.google.com/kml/2.2',  # Legacy Google namespace (deprecated but still found)
#    'http://earth.google.com/kml/2.1',  # Legacy Google namespace (deprecated but still found)
#    'http://earth.google.com/kml/2.0',  # Legacy Google namespace (deprecated but still found)
#}
#
## The root element name that identifies a KML document
#KML_ROOT_ELEMENT = 'kml'
#
#
#@validators.register("format_4114")
#class KMLValidator(VectorFileValidator):
#    """Validator for Keyhole Markup Language (KML) files.
#
#    Validates that a file conforms to the KML specification by checking:
#    1. The file is valid XML
#    2. The root element is 'kml' in a KML namespace
#    3. The structure contains valid KML features
#    """
#
#    def _get_extensions(self) -> List[str]:
#        return ['.kml', '.xml']
#
#    def _validate_open(self, file_format: Format, file_input: FileInput,
#                       validation_result: ValidationResult) -> ValidationResult:
#        """Validate that the file is valid KML per OGC specification."""
#        path: Path = file_input.get_path()
#
#        # Parse XML
#        try:
#            tree = ET.parse(str(path))
#            root = tree.getroot()
#        except ET.ParseError as exc:
#            validation_result.set_failure(
#                message=f"XML parse error: {exc}",
#                code="OPEN_FAILED",
#                details={"exception": str(exc)}
#            )
#            return validation_result
#        except Exception as exc:
#            validation_result.set_uncertainty(
#                message=f"Could not open/parse file: {exc}",
#                code="OPEN_ERROR",
#                details={"exception": str(exc)}
#            )
#            return validation_result
#
#        # Check if KML according to OGC specification
#        is_kml, error_details = self._is_kml_document(root)
#
#        if not is_kml:
#            validation_result.set_failure(
#                message="XML file does not conform to KML specification.",
#                code="NOT_KML",
#                details=error_details
#            )
#            return validation_result
#
#        # Validate with Fiona (optional, for geometry validation)
#        try:
#            import fiona
#        except ImportError as exc:
#            # KML validation succeeded based on structure,
#            # but we can't do deeper geometry validation without Fiona
#            validation_result.set_success(
#                message="File validated as KML (structure only, Fiona not available for geometry check).",
#                code="OPEN_OK_PARTIAL",
#                details=error_details
#            )
#            return validation_result
#
#        try:
#            # Try to open with Fiona to validate geometry
#            # Note: Fiona uses OGR driver which supports KML
#            print(fiona.supported_drivers)
#            with fiona.open(str(path)) as src:
#                _ = src.schema
#                _ = src.crs
#            validation_result.set_success(
#                message="File validated as KML.",
#                code="OPEN_OK",
#                details=error_details
#            )
#        except Exception as e:
#            validation_result.set_failure(
#                message=f"File has KML structure but Fiona cannot read it: {e}",
#                code="OPEN_FAILED",
#                details=error_details
#            )
#
#        return validation_result
#
#    def _is_kml_document(self, root: ET.Element) -> Tuple[bool, dict]:
#        """Check if the XML root element conforms to KML specification.
#
#        Per OGC KML specification and Abstract Test Suite (OGC 14-068r2, ATC-101):
#        - Root element MUST be 'kml'
#        - Root element MUST be in a KML namespace
#
#        Args:
#            root: The XML root element
#
#        Returns:
#            Tuple of (is_kml: bool, details: dict)
#        """
#        details = {}
#
#        # Extract namespace and local name from root element
#        namespace, local_name = self._split_tag(root.tag)
#
#        details['root_element'] = local_name
#        details['namespace'] = namespace or "none"
#
#        # Check 1: Root element must be 'kml'
#        if local_name != KML_ROOT_ELEMENT:
#            details['error'] = f"Root element is '{local_name}', expected '{KML_ROOT_ELEMENT}'"
#            details['expected_element'] = KML_ROOT_ELEMENT
#            return False, details
#
#        # Check 2: Root element must be in KML namespace
#        if not namespace or namespace not in KML_NAMESPACES:
#            details['error'] = f"Root element namespace is '{namespace}', expected one of: {list(KML_NAMESPACES)}"
#            details['expected_namespaces'] = list(KML_NAMESPACES)
#            return False, details
#
#        # Check if using legacy Google namespace (warn but accept)
#        if namespace in ['http://earth.google.com/kml/2.0',
#                         'http://earth.google.com/kml/2.1',
#                         'http://earth.google.com/kml/2.2']:
#            details[
#                'warning'] = f"Using legacy Google namespace '{namespace}'. Consider updating to OGC namespace 'http://www.opengis.net/kml/2.2'"
#
#        # All checks passed
#        return True, details
#
#    def _split_tag(self, tag: str) -> Tuple[Optional[str], str]:
#        """Split a qualified XML tag into (namespace, local_name).
#
#        Args:
#            tag: XML tag, either 'localname' or '{namespace}localname'
#
#        Returns:
#            Tuple of (namespace or None, local_name)
#        """
#        if '}' in tag:
#            namespace, local_name = tag.split('}')
#            namespace = namespace[1:]  # Remove leading '{'
#            return namespace, local_name
#        return None, tag
#
#    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
#                             validation_result: ValidationResult) -> ValidationResult:
#        """Validate geometry types in KML file."""
#        return validate_shape_type_with_fiona(file_format, file_input, validation_result)
