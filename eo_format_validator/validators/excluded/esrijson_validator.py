import json
from pathlib import Path
from typing import List, Set

from eo_format_validator.validators.vector_file_validator import VectorFileValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format, ShapeType
from eo_format_validator.registry import validators
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.crs_operations import compare_crs
from eo_format_validator.utils.shape_operations import normalize_geometry_to_shape_type


@validators.register("format_4105")
class EsriJSONValidator(VectorFileValidator):

    def get_shape_type(self):
        pass

    def _get_extensions(self) -> List[str]:
        return ['.json']

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        """Quick open check.
        Does not validate all features.
        """
        path: Path = file_input.get_path()

        try:
            with path.open("r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except json.JSONDecodeError as exc:
            validation_result.set_failure(
                message=f"Invalid JSON: {exc}",
                code="OPEN_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result
        except Exception as exc:
            validation_result.add_warning(
                message=f"Could not open/parse file: {exc}",
                code="OPEN_ERROR",
                details={"exception": str(exc)}
            )
            return validation_result

        # Basic GeoJSON checks
        top_type = doc.get("type") if isinstance(doc, dict) else None
        if top_type not in ("FeatureCollection", "Feature", "GeometryCollection", "FeatureCollection"):
            # allow also plain Geometry object (type present but not Feature/Collection)
            if not isinstance(doc, dict) or "type" not in doc:
                validation_result.set_failure(
                    message="Top-level JSON does not appear to be GeoJSON (missing 'type').",
                    code="NOT_GEOJSON"
                )
                return validation_result

        # Basic open successful
        validation_result.set_success(
            message="GeoJSON opened successfully.",
            code="OPEN_OK",
            details={"topology_type": top_type}
        )
        return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """Quick CRS check for GeoJSON.
           - If the file contains a 'crs' member, use it.
           - If the Format provides an expected CRS,
           compare and require a match.
        """
        path: Path = file_input.get_path()

        # load JSON quickly (no heavy validation)
        try:
            with path.open("r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception as exc:
            validation_result.add_warning(
                message=f"Could not parse GeoJSON for CRS detection: {exc}",
                code="CRS_PARSE_FAILED",
                details={"exception": str(exc)}
                )
            return validation_result

        crs = None
        if isinstance(doc, dict):
            crs = doc.get("crs")

        return compare_crs(crs, file_format, path, validation_result)

    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        """Quick shape type detection for GeoJSON.

        Gathers geometry types present in the document (top few features only)
        and maps them to high-level categories: point/line/polygon/other.
        If the Format provides an expected shape type, it is checked.
        """
        path: Path = file_input.get_path()

        try:
            with path.open("r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception as exc:
            validation_result.add_warning(
                message=f"Could not parse GeoJSON for shape detection: {exc}",
                code="SHAPE_PARSE_FAILED",
                details={"exception": str(exc)}
            )
            return validation_result

        found_geometries: Set[ShapeType] = set()

        # helper to inspect a geometry object
        def inspect_geometry(geom_obj: dict):
            if not isinstance(geom_obj, dict):
                return
            gtype = geom_obj.get("type")
            if not gtype:
                return
            found_geometries.add(normalize_geometry_to_shape_type(gtype))

        top_type = doc.get("type") if isinstance(doc, dict) else None
        if top_type == "FeatureCollection":
            for feat in doc.get("features", [])[:50]:  # sample up to first 50 features
                geom = feat.get("geometry") if isinstance(feat, dict) else None
                inspect_geometry(geom)
        elif top_type == "Feature":
            geom = doc.get("geometry")
            inspect_geometry(geom)
        elif isinstance(doc, dict) and doc.get("type"):
            # standalone geometry
            inspect_geometry(doc)

        if not found_geometries:
            validation_result.add_warning(
                message="No geometries detected in GeoJSON (or file empty).",
                code="NO_GEOMETRIES"
            )
            return validation_result

        validation_result.add_info(
            message="Geometry types detected in GeoJSON.",
            code="GEOM_TYPES_DETECTED",
            details={"geometries": sorted(list(found_geometries.__str__()))}
        )

        expected = file_format.get_shape_type()

        if expected:
            if expected not in found_geometries:
                validation_result.set_failure(
                    message=f"GeoJSON geometries {sorted(list(found_geometries.__str__()))} do not include expected '{expected}'.",
                    code="SHAPE_MISMATCH"
                )
                return validation_result
            else:
                validation_result.set_success(
                    message=f"GeoJSON contains expected shape type: '{expected}'.",
                    code="SHAPE_MATCH",
                    details={"found": sorted(list(found_geometries.__str__())), "expected": expected}
                )
        return validation_result



#----------------------optional further advanced checks-----------------------