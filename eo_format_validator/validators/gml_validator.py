"""Geography Markup Language, different from the Graph Modelling Language (also GML, same file extension).
   Documentation: https://portal.ogc.org/files/?artifact_id=46568"""
from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET

from eo_format_validator.validators.vector_file_validator import VectorFileValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.validator_registry import validators
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.shape_operations import validate_shape_type_with_fiona

# extend namespaces to allow further gml files deviating from the specification, e.g. platform-specific definitions
GML_NAMESPACES = {
    'http://www.opengis.net/gml',
    'http://www.opengis.net/gml/3.2',
    'http://www.opengis.net/gml/3.3',
}


@validators.register("format_4111")
class GMLValidator(VectorFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.gml', '.xml']

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        """Validate that the file is valid GML."""
        path: Path = file_input.get_path()

        # Parse XML
        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
        except ET.ParseError as exc:
            validation_result.set_failure(
                message=f"GML parse error: {exc}",
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

        # check if GML namespace according to specification
        namespace = self._extract_namespace(root)
        if not namespace or namespace not in GML_NAMESPACES:
            validation_result.set_failure(
                message="XML file does not appear to be GML.",
                code="NOT_GML",
                details={"namespace": namespace or "none", "expected": list(GML_NAMESPACES)}
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
            with fiona.open(str(path), driver='GML') as src:
                _ = src.schema
                _ = src.crs
            validation_result.set_success(
                message="File validated as GML.",
                code="OPEN_OK"
            )
        except Exception as e:
            validation_result.set_failure(
                message=f"File has GML structure but Fiona cannot read it: {e}",
                code="OPEN_FAILED"
            )

        return validation_result

    def _extract_namespace(self, root: ET.Element) -> str:
        """Extract namespace from root element. Check if XML has root element in GML namespace as defined in specification to differentiate from other XML files. Per OGC 10-129r1: GML is identified by its namespace.
           To allow further GML-based files, e.g. platform-specific like XPlanGML, allow for namespace to be present further below in the document."""
        tag = root.tag
        if '}' in tag:
            return tag.split('}')[0][1:]
        return None

    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        return validate_shape_type_with_fiona(file_format, file_input, validation_result)
