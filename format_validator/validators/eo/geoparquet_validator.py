"""https://geoparquet.org
   Specification: https://github.com/opengeospatial/geoparquet
   Stable: https://geoparquet.org/releases/v1.1.0/"""
from typing import List, Set,Optional
import pyarrow.parquet as pq
import geopandas as gpd
import json
from pyproj import CRS
from shapely import GeometryType

from ...model import ValidationResult,ValidationRequest, Error,Warning,Cause, FormatIdentifier
from .vector_file_validator import VectorFileValidator
from ...registry import registry


@registry.register(FormatIdentifier.GEOPARQUET)
class GeoParquetValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.parquet', '.geoparquet'] # .parquet recommended file ext., .geoparquet should not be used, but is used in practice

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        """Quick open check using pyarrow.parquet. Falls back to pandas.read_parquet.
           Accesses lightweight metadata: row_group_count, file metadata keys, schema
           field names. Does not read full datasets.
        """
        # try pyarrow.parquet first
        try:

            pf = pq.ParquetFile(str(request.actual_file.path))
            return ValidationResult.success(request)
        except Exception as exc_parquet:
            return ValidationResult.failure(request, Error(message=f"Could not open Parquet file with pyarrow:\n{exc_parquet}", cause=Cause.FILE_OPEN_ERROR))

    def get_crs(self, request: ValidationRequest) -> Optional[CRS]:
        """Find CRS candidate(s) in the GeoParquet file and compare them to the expected one."""
        # Try to read GeoParquet metadata via pyarrow.parquet to avoid loading data with geopandas
        try:
            meta = pq.ParquetFile(str(request.actual_file.path)).metadata
            # parquet file metadata key-value pairs are in .metadata.metadata as dict(bytes->bytes)
            kv = {}
            if meta and hasattr(meta, 'metadata') and meta.metadata:
                for k, v in meta.metadata.items():
                    try:
                        kv[k.decode('utf-8').lower()] = v.decode('utf-8')
                    except Exception:
                        # keep raw bytes as fallback
                        kv[k.decode('utf-8').lower()] = None

            geo_json = None
            # GeoParquet uses a 'geo' key with JSON content per spec
            if 'geo' in kv and kv['geo']:
                try:
                    geo_json = json.loads(kv['geo'])
                except Exception:
                    geo_json = None

            crs_val = None
            if geo_json:
                # top-level crs or per-column crs
                if 'crs' in geo_json:
                    crs_val = geo_json.get('crs')
                else:
                    # try columns -> find geometry column entry
                    cols = geo_json.get('columns') or {}
                    for colname, colmeta in cols.items():
                        if isinstance(colmeta, dict) and colmeta.get('geometry_type'):
                            crs_val = colmeta.get('crs') or colmeta.get('encoding')
                            if crs_val:
                                break

            # Interpret crs_val: look for formats like 'EPSG:4326' or integer
            if crs_val:
                try:
                    return CRS.from_user_input(crs_val)
                    # if isinstance(crs_val, int):
                    #     return EPSGCoordinateReferenceSystem(crs_val)
                    # if isinstance(crs_val, str) and crs_val.upper().startswith('EPSG:'):
                    #     epsg = int(crs_val.split(':', 1)[1])
                    #     return EPSGCoordinateReferenceSystem(epsg)
                except Exception:
                    pass
            return CRS.from_user_input("WGS84")  # default value is WGS84 if no CRS found in metadata
        except Exception:
            return None

    def get_geometry_types(self, request: ValidationRequest) -> List[GeometryType]:
        """Get all geometry types found in the GeoParquet file.
        
        Reads geometry type information from GeoParquet metadata.
        
        Args:
            request: The validation request containing the file to analyze
            
        Returns:
            List of GeometryType enum values found in the file
        """
        types = []
        try:
            metadata = pq.read_metadata(request.actual_file.path).metadata
            if b"geo" not in metadata:
                return types
            
            geo_meta = json.loads(metadata[b"geo"].decode("utf-8"))
            primary_col = geo_meta["primary_column"]
            geom_types = geo_meta["columns"][primary_col].get("geometry_types", [])
            
            # Convert string geometry types to GeometryType enum
            for gt in geom_types:
                try:
                    geom_type = GeometryType[gt.upper()]
                    types.append(geom_type)
                except (KeyError, AttributeError):
                    # Unknown geometry type, skip
                    pass
        except Exception:
            # Return empty list on error - let assert_geometry_type handle it
            pass
        
        return types
