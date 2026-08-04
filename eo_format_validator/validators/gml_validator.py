"""Geography Markup Language, different from the Graph Modelling Language (also GML, same file extension).
   Documentation: https://portal.ogc.org/files/?artifact_id=46568"""
from typing import List,Optional
import xml.etree.ElementTree as ET
import fiona

from ..model import ValidationRequest,ValidationResult,Error,Cause,Warning
from .vector_file_validator import VectorFileValidator
from ..registry import registry

# extend namespaces to allow further gml files deviating from the specification, e.g. platform-specific definitions
GML_NAMESPACES = {
    'http://www.opengis.net/gml',
    'http://www.opengis.net/gml/3.2',
    'http://www.opengis.net/gml/3.3',
}


@registry.register("format_4111")
class GMLValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.gml', '.xml']

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        """Validate that the file is valid GML."""
        # Parse XML
        try:
            tree = ET.parse(str(request.actual_file.path))
            root = tree.getroot()
        except ET.ParseError as exc:
            return ValidationResult.failure(
                request,
                Error(message=f"GML parse error: {exc}", cause=Cause.STRUCTURAL_MALFORMED)
            )
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                    Warning(message=f"Could not open/parse gml file: \n{exc}", cause=Cause.UNKNOWN)
            )


        # check if GML namespace according to specification
        namespace = self._extract_namespace(root)
        if not namespace or namespace not in GML_NAMESPACES:
            return ValidationResult.failure(
                request,
                Error(message=f"XML file does not appear to be GML. Root element namespace '{namespace}' is not in expected GML namespaces.", cause=Cause.STRUCTURAL_MALFORMED)
            )

        try:
            with fiona.open(str(request.actual_file.path), driver='GML') as src:
                _ = src.schema
                _ = src.crs
        except Exception as e:
            return ValidationResult.failure(
                request,
                Error(message=f"File has GML structure but Fiona cannot read it: \n{e}", cause=Cause.FILE_OPEN_ERROR)
            )
        return ValidationResult.success(request)

    def _extract_namespace(self, root: ET.Element) -> Optional[str]:
        """Extract namespace from root element. Check if XML has root element in GML namespace as defined in specification to differentiate from other XML files. Per OGC 10-129r1: GML is identified by its namespace.
           To allow further GML-based files, e.g. platform-specific like XPlanGML, allow for namespace to be present further below in the document."""
        tag = root.tag
        if '}' in tag:
            return tag.split('}')[0][1:]
        return None
