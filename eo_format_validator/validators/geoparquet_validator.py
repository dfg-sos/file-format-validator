"""https://geoparquet.org
   Specification: https://github.com/opengeospatial/geoparquet
   Stable: https://geoparquet.org/releases/v1.1.0/"""
from pathlib import Path
from typing import List, Set

from eo_format_validator.model import FileInput,Format,ShapeType,ValidationResult
from eo_format_validator.util import normalize_geometry_to_shape_type,compare_crs
from .vector_file_validator import VectorFileValidator
from ..registry import Registry

@Registry.register("format_4108")
class GeoParquetValidator(VectorFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.parquet', '.geoparquet'] # .parquet recommended file ext., .geoparquet should not be used, but is used in practice

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        """Quick open check using pyarrow.parquet. Falls back to pandas.read_parquet.
           Accesses lightweight metadata: row_group_count, file metadata keys, schema
           field names. Does not read full datasets.
        """
        path: Path = file_input.get_path()
        # try pyarrow.parquet first
        try:
            import pyarrow.parquet as pq
            pf = pq.ParquetFile(str(path))

            try:
                rg_count = pf.num_row_groups
            except Exception as e:
                rg_count = None
                validation_result.set_failure(
                    message="Could not open Parquet file with pyarrow.",
                    code="PARQUET_OPEN_FAILED",
                    details={"pyarrow_error": str(e)}
                )
                return validation_result
            try:
                cols = list(pf.schema.names)
            except Exception as e:
                validation_result.set_failure(
                    message="Could not open Parquet file with pyarrow.",
                    code="PARQUET_OPEN_FAILED",
                    details={"pyarrow_error": str(e)}
                )
                return validation_result

            validation_result.set_success(
                message="Parquet file opened for metadata inspection (pyarrow).",
                code="OPEN_OK",
                details={"row_groups": rg_count, "column_count": len(cols), "columns_sample": cols[:10]}
            )
            return validation_result

        except Exception as exc_parquet:
            # fall back to pandas read_parquet
            try:
                import pandas as pd
                df = pd.read_parquet(str(path))
                validation_result.set_success(
                    message="Parquet file opened via pandas.read_parquet.",
                    code="OPEN_OK_PANDAS",
                    details={"columns": list(df.columns)}
                )
                return validation_result

            except Exception as exc_pandas:
                validation_result.set_failure(
                    message="Could not open Parquet file with pyarrow or pandas.",
                    code="PARQUET_OPEN_FAILED",
                    details={"pyarrow_error": str(exc_parquet), "pandas_error": str(exc_pandas)}
                )
                return validation_result

    def assert_srs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        """Find CRS candidate(s) in the GeoParquet file and compare them to the expected one."""
        path: Path = file_input.get_path()
        crs = None
        # try geopandas if available: geopandas preserves geometry and crs reliably
        try:
            import geopandas as gpd
            gdf = gpd.read_parquet(str(path))
            if hasattr(gdf, "crs") and gdf.crs is not None:
                crs = gdf.crs
                #print(gdf.crs.name)
                #print(gdf.crs)
                #print(gdf.crs.to_authority())
                # print(gdf.to_crs("EPSG:4326").crs.to_epsg()) # this command can transform the crs to epsg 4326.
                # However, this is not our task and would provide an incorrect ValidationResult for a CWL user, if we change the crs representation and validate afterwards
                # in case of CRS84 (swapped lat/lon coordinates), we assume equality since applications are required to transform both as per spec definition
                if crs.name.__contains__("CRS84"):
                    #print("TRANSFORM")
                    crs="4326"
        except Exception:
            pass

        return compare_crs(crs, file_format, path, validation_result)


    def _validate_shape_type(self, file_format: Format, file_input: FileInput,
                             validation_result: ValidationResult) -> ValidationResult:
        """Quick geometry/shape hinting for GeoParquet.
           - Detect geometry column names.
           - If geopandas is available and a small read succeeds, inspect geometry types.
        """
        path: Path = file_input.get_path()

        geom_cols: List[str] = []
        categories: Set[ShapeType] = set()

        # try pyarrow schema for column names
        try:
            import pyarrow.parquet as pq
            pf = pq.ParquetFile(str(path))
            schema = pf.schema_arrow
            col_names = [f.name for f in schema]
            common_geom_names = {'geometry', 'geom', 'wkb', 'wkt', 'geometry_wkb', 'geometry_wkt'}
            geom_cols = [c for c in col_names if c.lower() in common_geom_names]
        except Exception:
            pass
        if not geom_cols:
            validation_result.set_uncertainty(
                message="No obvious geometry column detected in GeoParquet.",
                code="NO_GEOM_COLUMN"
            )
            return validation_result

        # if geopandas available, try reading small sample to inspect geometry types
        try:
            import geopandas as gpd
            try:
                # read only the geometry column(s) if possible to reduce IO
                gdf = gpd.read_parquet(str(path), columns=geom_cols)
                # sample geometry types
                for geom in gdf.geometry.head(50):
                    if geom is None:
                        continue
                    gname = geom.geom_type.lower() if hasattr(geom, 'geom_type') else None
                    if not gname and hasattr(geom, 'geom_type'):
                        gname = str(geom.geom_type).lower()
                    if gname:
                        categories.add(normalize_geometry_to_shape_type(gname))
            except Exception:
                # geopandas read failed, skip sampling
                pass
        except Exception:
            pass

        if categories:
            expected_shape_type = file_format.get_shape_type()
            if expected_shape_type is not None:
                if expected_shape_type in categories:
                    validation_result.set_success(
                        message="Expected shape type matches geometry.",
                        code="SHAPE_MATCH",
                        details={"geometries": categories}
                    )
                    return validation_result
                else:
                    validation_result.set_failure(
                        message="Expected shape type does not match geometry.",
                        code="SHAPE_MISMATCH",
                        details={"geometries": categories}
                    )
                    return validation_result
        else:
            validation_result.set_uncertainty(
                message="Could not determine geometry by sampling.",
                code="NO_GEOM"
            )
        return validation_result