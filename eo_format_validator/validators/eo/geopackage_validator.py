from typing import List, Optional, Dict
from attr import dataclass
from eo_format_validator.model import Info
import geopandas as gpd
import fiona
from pyproj import CRS
from shapely import GeometryType

from eo_format_validator.model import ValidationResult,ValidationRequest, Warning, Cause, Error
from .eo_file_format_validator import EOValidationRequest
from .raster_file_validator import RasterFileValidator
from .vector_file_validator import VectorFileValidator
from ...registry import registry


@registry.register("format_4107")
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
            return ValidationResult.failure(
                request,
                Error(message=f"Failed to query GeoPackage database: \n{exc}", cause=Cause.STRUCTURAL_MALFORMED)
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

    def get_crs(self, request: EOValidationRequest) -> Optional[CRS]:
        try:
            dfs = self._read(request)
            # Return CRS from first layer found
            for df in dfs:
                if hasattr(df, "crs") and df.crs:
                    return df.crs
            return None
        except Exception:
            return None

    def get_geometry_types(self, request: EOValidationRequest) -> List[GeometryType]:
        """Get all geometry types found in the GeoPackage file.
        
        Iterates through all layers and collects geometry types from vector layers.
        
        Args:
            request: The validation request containing the file to analyze
            
        Returns:
            List of GeometryType enum values found in the file
        """
        from .vector_file_validator import geometry_type_from_string
        types = set()
        try:
            dfs = self._read(request)
            for df in dfs:
                # Skip non-geometry layers
                if df.empty or getattr(df, "geometry", None) is None:
                    continue
                
                # Check if layer has any valid geometries
                if not df.geometry.notna().any():
                    continue
                
                # Get geometry types in this layer
                for geom in df.geometry:
                    if geom is not None and hasattr(geom, "geom_type"):
                        geom_type_str = geom.geom_type
                        geom_type = geometry_type_from_string(geom_type_str) if geom_type_str else None
                        if geom_type is not None:
                            types.add(geom_type)
        except Exception:
            # Return empty list on error - let assert_geometry_type handle it
            pass
        
        return list(types)

    def validate(self, request: ValidationRequest) -> ValidationResult:
        if self.has_vector_layers(request):
            return VectorFileValidator.validate(self, request)
        else:
            return RasterFileValidator.validate(self, request)
