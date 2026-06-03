from typing import List, Optional,Dict
from attr import dataclass
import geopandas as gpd
import fiona

from eo_format_validator.model import ValidationResult,ValidationRequest, Warning, Cause, Error,CoordinateReferenceSystem,EPSGCoordinateReferenceSystem
from eo_format_validator.model.validation_request import EOValidationRequest
from .raster_file_validator import RasterFileValidator
from .vector_file_validator import VectorFileValidator
from ..registry import Registry


@Registry.register("format_4107")
@dataclass
class GeoPackageValidator(VectorFileValidator, RasterFileValidator): # ensure correct use of _validate_open method, implementation of left parent is used due to MRO (https://docs.python.org/3/howto/mro.html)
    geopandas_dfs: Dict[str,List[gpd.GeoDataFrame]] = {}

    def _read(self, request: ValidationRequest) -> List[gpd.GeoDataFrame]:
        if self.geopandas_dfs.get(str(request.actual_file.path)) is not None:
            return self.geopandas_dfs[str(request.actual_file.path)]
        layers = fiona.listlayers(str(request.actual_file.path))
        dfs = []
        for layer in layers:
            df = gpd.read_file(str(request.actual_file.path), layer=layer)
            df.attrs["layer"] = layer
            dfs.append(df)
        self.geopandas_dfs[str(request.actual_file.path)] = dfs
        return dfs

    def get_extensions(self) -> List[str]:
        return ['.gpkg']

    @staticmethod
    def assert_gpkg_tables(request: ValidationRequest) -> ValidationResult:
        """
           Check required and recommended GeoPackage system tables.
            - Required tables: gpkg_contents, gpkg_spatial_ref_sys
            - Recommended tables: gpkg_extensions, gpkg_metadata, gpkg_metadata_reference
        """
        try:
            import sqlite3
            conn = sqlite3.connect(str(request.actual_file.path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row["name"] for row in cur.fetchall()}
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Failed to inspect GeoPackage SQLite file: \n{exc}", cause=Cause.UNKNOWN)
            )
        REQUIRED_TABLES = {"gpkg_contents", "gpkg_spatial_ref_sys"}
        RECOMMENDED_TABLES = {"gpkg_extensions", "gpkg_metadata", "gpkg_metadata_reference"}
        missing_required = REQUIRED_TABLES - tables
        if missing_required:
            return ValidationResult.failure(
                request,
                Error(message=f"GeoPackage missing required tables: {sorted(list(missing_required))}",cause=Cause.STRUCTURAL_MALFORMED)
            )
        missing_recommended = RECOMMENDED_TABLES - tables
        if missing_recommended:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"GeoPackage missing recommended tables: {sorted(list(missing_recommended))}", cause=Cause.STRUCTURAL_MALFORMED)
            )
        return ValidationResult.success(request)
    
    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        try:
            self.geopandas_df = self._read(request)
            return self.assert_gpkg_tables(request)
        except Exception as exc:
            return ValidationResult.failure(request,
                Error(message=f"Could not read GeoPackage file with Geopandas: \n{exc}", cause=Cause.FILE_OPEN_ERROR)
            )
        
    def has_vector_layers(self, request: ValidationRequest) -> bool:
        try:
            dfs = self._read(request)
            for df in dfs:
                if df.empty or getattr(df, "geometry", None) is None:
                    continue
                if df.geometry.notna().any():
                    return True
            return False
        except Exception:
            return False

    def get_crs(self, request: EOValidationRequest) -> Optional[CoordinateReferenceSystem]:
        pass

    def assert_crs(self, request: EOValidationRequest) -> ValidationResult:
        if request.crs is None:
            return ValidationResult.uncertain(request, Warning(message="No expected CRS provided, skipping CRS validation.", cause=Cause.MISSING_METADATA))
        try:
            dfs = self._read(request)
            def extract_epsg_from_gdf(gdf: gpd.GeoDataFrame) -> Optional[CoordinateReferenceSystem]:
                if hasattr(gdf, "crs") and gdf.crs:
                    epsg_code = gdf.crs.to_epsg()
                    return EPSGCoordinateReferenceSystem(epsg_code) if epsg_code is not None else None
                return None
            for df in dfs:
                crs = extract_epsg_from_gdf(df)
                layer_name = df.attrs.get("layer", "unknown_layer")
                if crs is None:
                    return ValidationResult.uncertain(request, Warning(message=f"Layer '{layer_name}' has no CRS defined, cannot validate against expected CRS.", cause=Cause.MISSING_METADATA))
                if crs != request.crs:
                    return ValidationResult.failure(request, Error(message=f"Layer '{layer_name}' CRS '{crs}' does not match expected CRS '{request.crs}'.", cause=Cause.METADATA_MISMATCH))
            return ValidationResult.success(request)
        except Exception as exc:
            return ValidationResult.uncertain(request, Warning(message=f"Failed to read CRS from GeoPackage with Geopandas: \n{exc}", cause=Cause.UNKNOWN))

    def validate(self, request: ValidationRequest) -> ValidationResult:
        if self.has_vector_layers(request):
            return VectorFileValidator.validate(self, request)
        else:
            return RasterFileValidator.validate(self, request)

    def assert_geometry_type(self, request: EOValidationRequest) -> ValidationResult:
        """
        Assert geometry types for each vector layer in the geopackage.
        - Iterate through all layers in the geopackage
        - For each layer, check if it has vector geometry
        - Validate against expected geometry type from the request
        - Return success if all vector layers match expected geometry type
        """
        try:
            if not hasattr(request, 'geometry_type') or request.geometry_type is None:
                return ValidationResult.uncertain(
                    request,
                    Warning(message="No expected geometry type provided, skipping geometry type validation.", cause=Cause.MISSING_METADATA)
                )
            
            dfs = self._read(request)
            layer_geometries = {}
            
            for df in dfs:
                layer_name = df.attrs.get("layer", "unknown_layer")
                
                # Skip non-geometry layers
                if df.empty or getattr(df, "geometry", None) is None:
                    continue
                
                # Check if layer has any valid geometries
                if not df.geometry.notna().any():
                    continue
                
                # Get geometry types in this layer
                geom_types = set()
                for geom in df.geometry:
                    if geom is not None and hasattr(geom, "geom_type"):
                        geom_types.add(geom.geom_type)
                
                if geom_types:
                    layer_geometries[layer_name] = geom_types
                    
                    # Validate against expected geometry type
                    if request.geometry_type not in geom_types:
                        return ValidationResult.failure(
                            request,
                            Error(message=f"Layer '{layer_name}' geometry type(s) {sorted(geom_types)} do not match expected geometry type '{request.geometry_type}'.", cause=Cause.METADATA_MISMATCH)
                        )
            
            if not layer_geometries:
                return ValidationResult.uncertain(
                    request,
                    Warning(message="No vector layers with valid geometries found in GeoPackage.", cause=Cause.STRUCTURAL_MALFORMED)
                )
            
            return ValidationResult.success(request)
            
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Failed to assert geometry types: \n{exc}", cause=Cause.UNKNOWN)
            )
