from typing import List


from eo_format_validator.model import Format,ValidationResult,MultiFileInput
from eo_format_validator.util import validate_shape_type_with_fiona
from .vector_file_validator import VectorFileValidator
from ..registry import Registry

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

@Registry.register("format_4119")
class ShapefileValidator(VectorFileValidator):
    """Shapefile validator, lightweight validation for ESRI Shapefiles:
        - extension check (.shp), additional files check (REQUIRED: .shp (geometry), .shx (index), .dbf (attributes), .prj (CRS)
        - OPTIONAL: .cpg, .sbn, .sbx, .shp.xml, .qix, etc.
        - quick open with fiona
        - CRS presence comparison to expected
        - geometry type detection and comparison with expected shape type

        No deep inspection of attributes or features is performed.
    """

    def _get_extensions(self) -> List[str]:
        return ['.shp']

    def _validate_extension(self, file_format: Format, multi_file_input: MultiFileInput, validation_result: ValidationResult) -> ValidationResult:
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
        validation_result = super()._validate_extension(file_format, multi_file_input, validation_result)

        # 2) If basic extension check failed, further checks not useful, return early
        if not validation_result.is_valid:
            return validation_result

        path = multi_file_input.get_path()
        secondary_files = multi_file_input.get_secondary_files()

        # 3) Get all available secondary file extensions, keys are not sufficient as CWL only stores type File
        available_extensions = set() #secondary_files.keys()

        for path in secondary_files:

            if path.name.lower().endswith('.shp.xml'):
                ext = '.shp.xml'
            else:
                ext = path.suffix.lower()
            available_extensions.add(ext)

        # 4) Check location of secondary files: all secondary files must be in the same directory as the .shp file
        wrong_dir = [f for f in secondary_files if f.parent != path.parent]
        if wrong_dir:
            validation_result.set_failure(
                message="Secondary files must be in the same directory as the .shp file",
                code="STRUCTURE_INVALID",
                details={'wrong_directory': [str(f) for f in wrong_dir]}
            )
            return validation_result

        # 5) Check REQUIRED files
        missing_required = REQUIRED_EXTENSIONS - available_extensions

        if missing_required:
            validation_result.set_failure(
                message=f"Missing required secondary files for EO Shapefile: {missing_required}",
                code="SEC_MISSING",
                details={"missing": missing_required, "actual_required": available_extensions}
            )
            return validation_result
        else:
            validation_result.set_success(
                message="All required Shapefile secondary files present.",
                code="SEC_OK",
                details={"Found:": available_extensions}
            )

        # 6) Identify OPTIONAL files present
        found_optional = available_extensions & OPTIONAL_EXTENSIONS

        if found_optional:
            validation_result.add_info(
                message=f"Shapefile has optional component file(s): {', '.join(sorted(found_optional))}",
                code="OPT_FOUND",
                details={'optional_files': sorted(list(found_optional))}
            )

        return validation_result

    def _validate_shape_type(self, file_format: Format, multi_file_input: MultiFileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        """Validate the geometry type of the Shapefile.
           Checks:
           - Geometry type is present
           - Geometry type equals expected shape type
        """
        return validate_shape_type_with_fiona(file_format, multi_file_input, validation_result)


#----------------------optional further advanced checks-----------------------



