from typing import List
from shapely import GeometryType
import fiona

from format_validator.model import ValidationRequest,ValidationResult,Error,Cause,Info,FormatIdentifier
from .vector_file_validator import VectorFileValidator, geometry_type_from_string
from ...registry import registry

# Define required, recommended, and optional Shapefile components
REQUIRED_EXTENSIONS = {'.shx', '.dbf', '.prj'} # .shp is also required, but checked separately
OPTIONAL_EXTENSIONS = {
    '.cpg',  # Code page (encoding)
    '.sbn',  # Spatial index
    '.sbx',  # Spatial index
    '.shp.xml',  # Metadata
    '.qix',  # QGIS spatial index
    '.qpj',  # QGIS projection
    '.fbn',  # Read-only spatial index
    '.fbx',  # Read-only spatial index
    '.ain',  # Attribute index
    '.aih',  # Attribute index
    '.atx',  # Attribute index
    '.ixs',  # Geocoding index
    '.mxs'  # Geocoding index
}

@registry.register(FormatIdentifier.SHAPEFILE)
class ShapefileValidator(VectorFileValidator):
    """Shapefile validator, lightweight validation for ESRI Shapefiles:
        - extension check (.shp), additional files check (REQUIRED: .shp (geometry), .shx (index), .dbf (attributes), .prj (CRS)
        - OPTIONAL: .cpg, .sbn, .sbx, .shp.xml, .qix, etc.
        - quick open with fiona
        - CRS presence comparison to expected
        - geometry type detection and comparison with expected shape type

        No deep inspection of attributes or features is performed.
    """

    def get_extensions(self) -> List[str]:
        return ['.shp']

    def assert_extension(self, request: ValidationRequest) -> ValidationResult:
        """Override for multi-file formats.
           For EO file formats, we require .shp, .dbf, .shx, and .prj to be present.

            Expected inputs:
            - the main .shp Path is provided as input_file.get_path()
            - auxiliary files (.shx, .dbf, .prj) are passed in
              input_file.secondary_files as Dict[str, Path]

            This method checks:
            - that the main file has a .shp extension
            - that the required auxiliary files (.shx, .dbf, .prj) exist among
              the provided secondary_files
            - identifies additional auxiliary files provided and reports them in an info
        """

        # 1) First, validate the main .shp extension
        validation_result = super().assert_extension(request=request)

        # 2) If basic extension check failed, further checks not useful, return early
        if not validation_result:
            return validation_result

        path = request.actual_file.path
        secondary_files = request.actual_file.files() - {path}  # Get all secondary files by excluding the main .shp file

        # 3) Get all available secondary file extensions, keys are not sufficient as CWL only stores type File
        available_extensions = set()
        for p in secondary_files:
            if p.name.lower().endswith('.shp.xml'):
                ext = '.shp.xml'
            else:
                ext = p.suffix.lower()
            available_extensions.add(ext)

        # 4) Check location of secondary files: all secondary files must be in the same directory as the .shp file
        if any([f for f in secondary_files if f.parent != path.parent]):
            return ValidationResult.failure(
                request,
                Error(message="Secondary files must be in the same directory as the .shp file", cause=Cause.STRUCTURAL_MALFORMED)
            )
        # 5) Check REQUIRED files
        missing_required = REQUIRED_EXTENSIONS - available_extensions

        if missing_required:
            return ValidationResult.failure(
                request,
                Error(message=f"Missing required secondary files for EO Shapefile: {missing_required}", cause=Cause.STRUCTURAL_MALFORMED)
            )
        # 6) Identify OPTIONAL files present
        found_optional = available_extensions & OPTIONAL_EXTENSIONS
        if found_optional:
            validation_result.add(Info(f"Shapefile has optional file(s): {', '.join(sorted(found_optional))}"))
        return validation_result

    def get_geometry_types(self, request) -> List[GeometryType]:
        """Get geometry types from the Shapefile's declared schema.
        
        Uses Fiona's layer schema geometry type declaration rather than
        iterating individual features. This is more reliable across GDAL
        versions, as different OGR builds may report feature-level geometry
        types differently (e.g., MultiPolygon vs Polygon for the same file).
        """
        try:
            with fiona.open(str(request.actual_file.path)) as ds:
                geom_type_str = ds.schema.get('geometry')
                geom_type = geometry_type_from_string(geom_type_str)
                return [geom_type] if geom_type is not None else []
        except Exception:
            # Return empty list on error - let assert_geometry_type handle it
            return []