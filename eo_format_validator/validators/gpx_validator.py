"""GPX (GPS Exchange Format), Sepcification: V1.1 https://www.topografix.com/GPX/1/1/gpx-strict.xsd,
                                             V1.0 https://www.topografix.com/GPX/1/0/gpx-strict.xsd"""
from pathlib import Path
from typing import List, Tuple, Optional
import xml.etree.ElementTree as ET

from eo_format_validator.model import FileInput, Format, ValidationResult
from .vector_file_validator import VectorFileValidator
from ..registry import Registry
from eo_format_validator.util import validate_shape_type_with_fiona

GPX_NAMESPACES = {
        'http://www.topografix.com/GPX/1/0',  # GPX 1.0
        'http://www.topografix.com/GPX/1/1',  # GPX 1.1
    }

# the required root element name that identifies a GPX document
GPX_ROOT_ELEMENT = 'gpx'

@Registry.register("format_4112")
class GPXValidator(VectorFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.gpx']

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        """Validate that the file is valid GPX per specification."""
        path: Path = file_input.get_path()

        # parse XML
        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
        except ET.ParseError as exc:
            validation_result.set_failure(
                message=f"GPX parse error: {exc}",
                code="OPEN_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Could not open/parse file: {exc}",
                code="OPEN_ERROR",
                details={"exception": str(exc)}
            )
            return validation_result

        # check if GPX according to specification
        is_gpx, error_details = self._is_gpx_document(root)

        if not is_gpx:
            validation_result.set_failure(
                message="XML file does not conform to GPX specification.",
                code="NOT_GPX",
                details=error_details
            )
            return validation_result

        # validate with Fiona
        try:
            import fiona
        except ImportError as exc:
            validation_result.set_uncertainty(
                message="The validator requires 'fiona' to be installed.",
                code="FIONA_MISSING",
                details={"exception": str(exc)}
            )
            return validation_result

        try:
            with fiona.open(str(path), driver='GPX') as src:
                _ = src.schema
                _ = src.crs
            validation_result.set_success(
                message="File validated as GPX.",
                code="OPEN_OK",
                details=error_details
            )
        except Exception as e:
            validation_result.set_failure(
                message=f"File has GPX structure but Fiona cannot read it: {e}",
                code="OPEN_FAILED",
                details=error_details
            )

        return validation_result

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

    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        """Validate geometry types in GPX file."""
        return validate_shape_type_with_fiona(file_format, file_input, validation_result)

