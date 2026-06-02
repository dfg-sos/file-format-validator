import json
from pathlib import Path
from typing import List, Set

from eo_format_validator.util import normalize_geometry_to_shape_type,compare_crs
from eo_format_validator.model import FileInput,Format,ShapeType,ValidationResult
from ..registry import Registry
from .vector_file_validator import VectorFileValidator

@Registry.register("format_4106")
class GeoJSONValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.geojson', '.json']

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
            validation_result.set_uncertainty(
                message=f"Could not open/parse file: {exc}",
                code="OPEN_ERROR",
                details={"exception": str(exc)}
            )
            return validation_result

        # basic GeoJSON checks
        top_type = doc.get("type") if isinstance(doc, dict) else None
        if top_type not in ("FeatureCollection", "Feature", "GeometryCollection", "FeatureCollection"):

            # also allow plain geometry object (type present but not Feature/Collection)
            if not isinstance(doc, dict) or "type" not in doc:
                validation_result.set_failure(
                    message="Top-level JSON does not appear to be GeoJSON (missing 'type').",
                    code="NOT_GEOJSON"
                )
                return validation_result

        # basic open successful
        validation_result.set_success(
            message="GeoJSON opened successfully.",
            code="OPEN_PASSED",
            details={"topology_type": top_type}
        )
        return validation_result

    def assert_srs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """Quick CRS check for GeoJSON.
           - If the file contains a 'crs' member, use it.
           - If the Format provides an expected CRS,
           compare for a match.
        """
       # path: Path = file_input.get_path()
#
       # # load JSON quickly (no heavy validation)
       # try:
       #     with path.open("r", encoding="utf-8") as fh:
       #         doc = json.load(fh)
       # except Exception as exc:
       #     validation_result.set_uncertainty(
       #         message=f"Could not parse GeoJSON for CRS detection: {exc}",
       #         code="CRS_FAILED",
       #         details={"exception": str(exc)}
       #         )
       #     return validation_result
#
       # crs = None
       # if isinstance(doc, dict):
       #     crs = doc.get("crs")
#
       # return compare_crs(crs, file_format, path, validation_result)

        path: Path = file_input.get_path()
        crs = None

        # try geopandas if available, geopandas preserves geometry and crs reliably
        try:
            import geopandas as gpd
            gdf = gpd.read_file(str(path))
            if hasattr(gdf, "crs"):
                crs = gdf.crs
            # print(gdf.crs.name)
            #print(gdf.crs)
            #print(gdf.geometry)
            # print(gdf.crs.to_authority())
            # print(gdf.to_crs("EPSG:4326").crs.to_epsg()) # this command can transform the crs to epsg 4326. However, this is not our task and would provide an incorrect ValidationResult for a CWL user, if we change the crs representation and validate afterwards

        except Exception:
            pass

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
            validation_result.set_uncertainty(
                message=f"Could not parse GeoJSON for shape detection: {exc}",
                code="SHAPE_FAILED",
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
            validation_result.set_uncertainty(
                message="No geometries detected in GeoJSON (or file empty).",
                code="NO_SHAPES"
            )
            return validation_result

        validation_result.add_info(
            message="Geometry types detected in GeoJSON.",
            code="SHAPE_FOUND",
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