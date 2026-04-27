from pathlib import Path
from typing import List

from eo_format_validator.validators.raster_file_validator import RasterFileValidator
from eo_format_validator.validators.vector_file_validator import VectorFileValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.validator_registry import validators
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.shape_operations import normalize_geometry_to_shape_type, compare_shape_type


@validators.register("format_4107")
class GeoPackageValidator(VectorFileValidator, RasterFileValidator): # ensure correct use of _validate_open method, implementation of left parent is used due to MRO (https://docs.python.org/3/howto/mro.html)

    def _get_extensions(self) -> List[str]:
        return ['.gpkg']

    def _validate_extension(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:

        super()._validate_extension(file_format, file_input, validation_result)
        self._validate_gpkg_tables(file_input, validation_result)

        # decide validated status according to unfinished validation steps: one uncertainty invalidates other valid partial results
        if validation_result.get_validated() and validation_result.get_uncertain() and validation_result.is_valid:
            validation_result.invalidate()

        return validation_result

    @staticmethod
    def _validate_gpkg_tables(file_input: FileInput,
                              validation_result: ValidationResult) -> ValidationResult:
        """
           Check required and recommended GeoPackage system tables.
            - Required tables: gpkg_contents, gpkg_spatial_ref_sys
            - Recommended tables: gpkg_extensions, gpkg_metadata, gpkg_metadata_reference
        """
        path = file_input.get_path()

        # open sqlite and list tables
        try:
            import sqlite3
            conn = sqlite3.connect(str(path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row["name"] for row in cur.fetchall()}
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Failed to inspect GeoPackage SQLite file: {exc}",
                code="SQLITE_OPEN_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result

        # Required & recommended
        required_tables = {"gpkg_contents", "gpkg_spatial_ref_sys"}
        recommended_tables = {"gpkg_extensions", "gpkg_metadata", "gpkg_metadata_reference"}

        missing_required = required_tables - tables
        if missing_required:
            # hard error if core gpkg tables missing
            validation_result.set_failure(
                message=f"GeoPackage missing required tables: {sorted(list(missing_required))}",
                code="GPKG_REQUIRED_MISSING",
                details={"missing": sorted(list(missing_required))}
            )
            # still continue to collect more info
        # warn for recommended missing
        missing_recommended = recommended_tables - tables
        if missing_recommended:
            validation_result.set_uncertainty(
                message=f"GeoPackage missing recommended tables: {sorted(list(missing_recommended))}",
                code="GPKG_RECOMMENDED_MISSING",
                details={"missing": sorted(list(missing_recommended))}
            )
        # further checks possible but not necessary for our use case
        validation_result.set_success(
            message=f"GeoPackage contains all required and recommended tables.",
            code="TABLES_PASSED"
        )
        return validation_result

    def _detect_gpkg_type(self, path: Path) -> str:
        """Inspect gpkg_contents.data_type"""
        # open sqlite and examine data_type

        import sqlite3
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute("SELECT data_type FROM gpkg_contents")
        data_types = {row[0] for row in cur.fetchall()}

        is_raster = 'tiles' in data_types or '2d-gridded-coverage' in data_types
        is_vector = 'features' in data_types

        if is_raster and not is_vector:
            return 'raster'
        elif is_vector and not is_raster:
            return 'vector'
        else:
            return 'unknown'

    def _validate_open(self, file_format, file_input, validation_result):
        try:
            gpkg_type = self._detect_gpkg_type(file_input.get_path())

            if gpkg_type == 'raster':
                return RasterFileValidator._validate_open(self, file_format, file_input, validation_result)
            elif gpkg_type == 'vector':
                return VectorFileValidator._validate_open(self, file_format, file_input, validation_result)
            else:
                validation_result.set_uncertainty(
                    message="Could not determine whether the GeoPackage contains raster or vector data.",
                    code="GPKG_KIND_UNKNOWN",
                    path=str(file_input.get_path())
                )
                return validation_result

        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Failed to inspect GeoPackage SQLite file: {exc}",
                code="SQLITE_OPEN_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput, validation_result: ValidationResult) -> ValidationResult:
        """If file does not use a crs, only add info and return."""
        try:
            gpkg_type = self._detect_gpkg_type(file_input.get_path())

            if gpkg_type == 'raster':
                return RasterFileValidator._validate_crs(self, file_format, file_input, validation_result)
            elif gpkg_type == 'vector':
                return VectorFileValidator._validate_crs(self, file_format, file_input, validation_result)
            else:
                validation_result.set_uncertainty(
                    message="Could not determine whether the GeoPackage contains raster or vector data.",
                    code="GPKG_KIND_UNKNOWN",
                    path=str(file_input.get_path())
                )
                return validation_result

        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Failed to inspect GeoPackage SQLite file: {exc}",
                code="SQLITE_OPEN_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result

    def _validate_strict(self, file_format: Format, file_input: FileInput,
                         validation_result: ValidationResult) -> ValidationResult:
        """Combination of all other validation methods, merging ValidationResults."""

        # validated hier nur true wenn alle validated wurden oder fehler gefunden und sonstiges (warnung)

        try:
            gpkg_type = self._detect_gpkg_type(file_input.get_path())

            if gpkg_type == 'raster':
                self._validate_extension(file_format, file_input, validation_result)
                RasterFileValidator._validate_open(self, file_format, file_input, validation_result)
                RasterFileValidator._validate_crs(self, file_format, file_input, validation_result)

            elif gpkg_type == 'vector':
                self._validate_extension(file_format, file_input, validation_result)
                VectorFileValidator._validate_open(self, file_format, file_input, validation_result)
                VectorFileValidator._validate_crs(self, file_format, file_input, validation_result)
                self._validate_shape_type(file_format, file_input, validation_result)

            else:
                validation_result.set_uncertainty(
                    message="Could not determine whether the GeoPackage contains raster or vector data.",
                    code="GPKG_KIND_UNKNOWN",
                    path=str(file_input.get_path())
                )
                return validation_result

        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"Failed to inspect GeoPackage SQLite file: {exc}",
                code="SQLITE_OPEN_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result

        # decide validated status according to unfinished validation steps: one uncertainty invalidates other validated partial results
        if validation_result.get_validated() and validation_result.get_uncertain() and validation_result.is_valid:
            validation_result.invalidate()

        return validation_result

    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        """
        Efficient shape-type check:
        - open gpkg, iterate layers (fiona.listlayers)
        - for each layer: first check schema['geometry']
          - success, if schema indicates the expected type
          - otherwise, sample up to N features and inspect feature['geometry']['type']
        - success, if expected type is found at least once in any layer
        - if no expected provided, collect detected categories and return info
        """

        try:
            import fiona
            from fiona.errors import DriverError
        except Exception as exc:
            validation_result.set_uncertainty(
                message=f"The GeoPackage validator requires the 'fiona' library to be installed.",
                code="FIONA_MISSING",
                details={"exception": str(exc)}
            )
            return validation_result

        # get expected shape type if present
        try:
            expected_shape = file_format.get_shape_type()
        except Exception:
            expected_shape = None

        path = file_input.get_path()
        try:
            # get a list of layer names for gpkg
            try:
                layers = fiona.listlayers(str(path))
            except Exception:
                # if listlayers fails (for older fiona version), try opening single layer
                layers = []

            geometries_found = set()
            found_expected = False
            shape_found = None
            max_samples_per_layer = 50

            for layer in layers:
                try:
                    with fiona.open(str(path)) as src:
                        geometry_found = src.schema.get("geometry") if getattr(src, "schema", None) else None
                        shape_found = normalize_geometry_to_shape_type(geometry_found)
                        if shape_found:
                            geometries_found.add(shape_found)
                            if expected_shape and expected_shape.__eq__(shape_found):
                                found_expected = True
                        if not found_expected:
                            # sample features up to N
                            count = 0
                            for feat in src:
                                count += 1
                                geometry_obj = feat.get("geometry")
                                if geometry_obj and isinstance(geometry_obj, dict):
                                    geometry_type = geometry_obj.get("type")
                                    shape_found = normalize_geometry_to_shape_type(geometry_type)
                                    if shape_found:
                                        geometries_found.add(shape_found)
                                        if expected_shape and expected_shape.__eq__(shape_found):
                                            found_expected = True
                                            break
                                if count >= max_samples_per_layer:
                                    break
                            if found_expected:
                                break
                except DriverError as e:
                    # skip problematic layer
                    validation_result.set_uncertainty(
                        message=f"Failed to open layer {layer}: {str(e)}",
                        code="LAYER_ERROR",
                        path=str(path)
                    )
                    return validation_result
                except Exception as e:
                    # skip problematic layer
                    validation_result.set_uncertainty(
                        message=f"Failed to open layer {layer}: {str(e)}",
                        code="LAYER_ERROR",
                        path=str(path)
                    )
                    return validation_result

            validation_result.add_info(message=f"Geometries found: {geometries_found.__str__()}")
            return compare_shape_type(expected_shape, shape_found, validation_result)

        except Exception as e:
            validation_result.set_uncertainty(
                message=f"Unexpected error during GeoPackage shape type validation: {str(e)}",
                code="SHAPE_ERROR",
                path=str(path),
                details={'error': str(e), 'error_type': type(e).__name__}
            )
            return validation_result

        #path = input_file.get_path()

        #try:
        #    import fiona
        #    from fiona.get_errors() import DriverError
        #except Exception as exc:
        #    validation_result.add_error(
        #        message=f"The GeoPackage validator requires the 'fiona' library to be installed.",
        #        code="FIONA_MISSING",
        #        details={"exception": str(exc)}
        #    )
        #    return validation_result

        #identifier = file_format.get_identifier()
        #try:
        #    with fiona.open(path) as src:
        #        schema = src.schema
        #        geometry_type = schema.get('geometry', None)

        #        if not geometry_type:
        #            validation_result.add_error(
        #                message=f"GeoPackage {identifier} has no geometry type defined",
        #                code="GEOMETRY_TYPE_MISSING",
        #                path=str(path)
        #            )
        #            return validation_result
        #        expected_shape = file_format.get_shape_type()
        #        # Check if geometry type corresponds to shape type
        #        if geometry_type == expected_shape:
        #            validation_result.add_info(
        #                message=f"File {identifier} has a valid shape type: {geometry_type}",
        #                code="SHAPE_VALID",
        #                path=str(path)
        #            )
        #            return validation_result
        #        else:
        #            # Mismatch otherwise
        #            validation_result.add_error(
        #                message=f"Geometry type of {identifier} does not match shape type.",
        #                code="SHAPE_MISMATCH",
         #               details={'shape_type': expected_shape, 'geometry_type': str(geometry_type)}
        #            )
        #            return validation_result

        #except DriverError as e:
        #    validation_result.add_error(
        #        message=f"Failed to read geometry type from GeoPackage: {str(e)}",
        #        code="GEOMETRY_TYPE_READ_FAILED",
        #        path=str(path),
         #       details={'error': str(e)}
        #    )
        #    return validation_result
        #except Exception as e:
        #    validation_result.add_error(
        #        message=f"Unexpected error while validating geometry type: {str(e)}",
        #        code="GEOMETRY_TYPE_ERROR",
        #        path=str(path),
        #        details={'error': str(e), 'error_type': type(e).__name__}
        #    )
        #    return validation_result



#----------------------optional further advanced checks-----------------------