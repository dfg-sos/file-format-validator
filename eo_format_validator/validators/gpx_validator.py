"""GPX (GPS Exchange Format), Sepcification: V1.1 https://www.topografix.com/GPX/1/1/gpx-strict.xsd,
                                             V1.0 https://www.topografix.com/GPX/1/0/gpx-strict.xsd"""
from typing import List, Tuple, Optional
import xml.etree.ElementTree as ET
import fiona

from eo_format_validator.model import ValidationRequest, ValidationResult,Error,Cause,Warning
from .vector_file_validator import VectorFileValidator
from ..registry import Registry

GPX_NAMESPACES = {
        'http://www.topografix.com/GPX/1/0',  # GPX 1.0
        'http://www.topografix.com/GPX/1/1',  # GPX 1.1
    }

# the required root element name that identifies a GPX document
GPX_ROOT_ELEMENT = 'gpx'

@Registry.register("format_4112")
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
            return validation_result
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

