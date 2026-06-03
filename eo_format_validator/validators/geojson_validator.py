from typing import List

from ..registry import Registry
from .vector_file_validator import VectorFileValidator

@Registry.register("format_4106")
class GeoJSONValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.geojson', '.json']

    # def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
    #     try:
    #         gpd.read_file(str(request.actual_file.path))
    #     except Exception as exc:
    #         return ValidationResult.failure(request,
    #             Error(message=f"Could not open/parse GeoJSON with Geopandas: \n{exc}", cause=Cause.STRUCTURAL_MALFORMED))
    #     return ValidationResult.success(request)

    # def get_crs(self, request: ValidationRequest) -> Optional[CoordinateReferenceSystem]:
    #     try:
    #         gdf = gpd.read_file(str(request.actual_file.path))
    #         if hasattr(gdf, "crs"):
    #             epsg_code = gdf.crs.to_epsg() if gdf.crs else None
    #             return EPSGCoordinateReferenceSystem(epsg_code) if epsg_code is not None else None
    #     except Exception:
    #         pass
    #     return None

    # def _validate_shape_type(self, file_format: Format, file_input: FileInput,
    #                          validation_result: ValidationResult) -> ValidationResult:
    #     """Quick shape type detection for GeoJSON.

    #        Gathers geometry types present in the document (top few features only)
    #        and maps them to high-level categories: point/line/polygon/other.
    #        If the Format provides an expected shape type, it is checked.
    #     """
    #     path: Path = file_input.get_path()

    #     try:
    #         with path.open("r", encoding="utf-8") as fh:
    #             doc = json.load(fh)
    #     except Exception as exc:
    #         validation_result.set_uncertainty(
    #             message=f"Could not parse GeoJSON for shape detection: {exc}",
    #             code="SHAPE_FAILED",
    #             details={"exception": str(exc)}
    #         )
    #         return validation_result

    #     found_geometries: Set[ShapeType] = set()

    #     # helper to inspect a geometry object
    #     def inspect_geometry(geom_obj: dict):
    #         if not isinstance(geom_obj, dict):
    #             return
    #         gtype = geom_obj.get("type")
    #         if not gtype:
    #             return
    #         found_geometries.add(normalize_geometry_to_shape_type(gtype))

    #     top_type = doc.get("type") if isinstance(doc, dict) else None
    #     if top_type == "FeatureCollection":
    #         for feat in doc.get("features", [])[:50]:  # sample up to first 50 features
    #             geom = feat.get("geometry") if isinstance(feat, dict) else None
    #             inspect_geometry(geom)
    #     elif top_type == "Feature":
    #         geom = doc.get("geometry")
    #         inspect_geometry(geom)
    #     elif isinstance(doc, dict) and doc.get("type"):
    #         # standalone geometry
    #         inspect_geometry(doc)

    #     if not found_geometries:
    #         validation_result.set_uncertainty(
    #             message="No geometries detected in GeoJSON (or file empty).",
    #             code="NO_SHAPES"
    #         )
    #         return validation_result

    #     validation_result.add_info(
    #         message="Geometry types detected in GeoJSON.",
    #         code="SHAPE_FOUND",
    #         details={"geometries": sorted(list(found_geometries.__str__()))}
    #     )

    #     expected = file_format.get_shape_type()
    #     if expected:
    #         if expected not in found_geometries:
    #             validation_result.set_failure(
    #                 message=f"GeoJSON geometries {sorted(list(found_geometries.__str__()))} do not include expected '{expected}'.",
    #                 code="SHAPE_MISMATCH"
    #             )
    #             return validation_result
    #         else:
    #             validation_result.set_success(
    #                 message=f"GeoJSON contains expected shape type: '{expected}'.",
    #                 code="SHAPE_MATCH",
    #                 details={"found": sorted(list(found_geometries.__str__())), "expected": expected}
    #             )
    #     return validation_result