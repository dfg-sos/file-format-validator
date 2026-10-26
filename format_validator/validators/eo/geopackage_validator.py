import sqlite3
from contextlib import closing
from pathlib import Path
from typing import List, Optional, Tuple
import fiona
from pyproj import CRS
from shapely import GeometryType

from format_validator.model import Info, ValidationResult, ValidationRequest, ValidationMode, Cause, Error, FormatIdentifier
from .eo_file_format_validator import geometry_type_from_string
from .raster_file_validator import RasterFileValidator
from .vector_file_validator import VectorFileValidator, sample_geometry_types
from ...registry import registry


@registry.register(FormatIdentifier.GEOPACKAGE)
class GeoPackageValidator(VectorFileValidator, RasterFileValidator): # ensure correct use of _validate_open method, implementation of left parent is used due to MRO (https://docs.python.org/3/howto/mro.html)
    """Validates a GeoPackage by its declarations, not its features: the layers, the geometry type
    each layer declares (gpkg_geometry_columns) and their CRS, read through fiona without loading
    features. This keeps the cost independent of the file size, like the Shapefile validator reading
    the header. Only a layer declaring the generic GEOMETRY type has its features sampled.
    A GeoPackage without vector layers is validated as a raster through rasterio."""

    def get_extensions(self) -> List[str]:
        return ['.gpkg']

    def __init__(self):
        super().__init__()
        # Layer declarations read for the running validate() call only, cleared when it returns.
        self._declared: Optional[List[Tuple[str, Optional[str], Optional[str]]]] = None

    @staticmethod
    def _read_declarations(request: ValidationRequest) -> List[Tuple[str, Optional[str], Optional[str]]]:
        """(layer, declared geometry type, CRS as WKT) of every layer; opens the layers, reads no features."""
        path = str(request.actual_file.path)
        declared = []
        for layer in fiona.listlayers(path):
            with fiona.open(path, layer=layer) as ds:
                declared.append((layer, ds.schema.get("geometry"), ds.crs.to_wkt() if ds.crs else None))
        return declared

    def _declarations(self, request: ValidationRequest) -> List[Tuple[str, Optional[str], Optional[str]]]:
        return self._declared if self._declared is not None else self._read_declarations(request)

    def _vector_layers(self, request: ValidationRequest) -> List[Tuple[str, str, Optional[str]]]:
        """Layers declaring a geometry column; attribute-only tables and raster tiles are left out."""
        return [d for d in self._declarations(request) if d[1] not in (None, "None")]

    @staticmethod
    def assert_gpkg_tables(request: ValidationRequest) -> ValidationResult:
        """
           Check required and recommended GeoPackage system tables.
            - Required tables: gpkg_contents, gpkg_spatial_ref_sys
            - Recommended tables: gpkg_extensions, gpkg_metadata, gpkg_metadata_reference
        """
        try:
            # as_uri() escapes characters like '#' and '?' that would otherwise end the path
            uri = Path(request.actual_file.path).resolve().as_uri() + "?mode=ro"
            with closing(sqlite3.connect(uri, uri=True)) as conn:
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
            # Optional in the GeoPackage specification, GDAL only creates them when they are used.
            return ValidationResult.success(
                request,
                Info(message=f"GeoPackage has no optional tables: {sorted(list(missing_recommended))}")
            )
        return ValidationResult.success(request)

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        result = self.assert_gpkg_tables(request)
        if not result or self.has_vector_layers(request):
            return result
        # Fiona found no vector layer, so the GeoPackage must hold raster tiles
        return result + RasterFileValidator.assert_can_open(self, request)

    def has_vector_layers(self, request: ValidationRequest) -> bool:
        try:
            return bool(self._vector_layers(request))
        except Exception:
            return False

    def get_crs(self, request: ValidationRequest) -> Optional[CRS]:
        if not self.has_vector_layers(request):
            return RasterFileValidator.get_crs(self, request)
        try:
            # CRS of the first vector layer that declares one
            for _, _, crs in self._vector_layers(request):
                if crs:
                    return CRS.from_user_input(crs)
            return None
        except Exception:
            return None

    def get_geometry_types(self, request: ValidationRequest) -> List[GeometryType]:
        """Get the geometry types the vector layers declare.

        Like the Shapefile validator, this uses the declared geometry type instead of the features.
        A layer declaring the generic GEOMETRY type (Fiona: "Unknown") may hold any type, so its
        features are sampled like in VectorFileValidator.

        Args:
            request: The validation request containing the file to analyze

        Returns:
            List of GeometryType enum values declared in (or, for generic layers, sampled from) the file
        """
        path = str(request.actual_file.path)
        types = set()
        try:
            for layer, geom_type_str, _ in self._vector_layers(request):
                if geom_type_str != "Unknown":
                    types.add(geometry_type_from_string(geom_type_str.removeprefix("3D ")))
                    continue
                with fiona.open(path, layer=layer) as ds:
                    types.update(sample_geometry_types(ds))
        except Exception:
            # Return empty list on error - let assert_geometry_type handle it
            pass

        return list(types)

    def validate(self, request: ValidationRequest) -> ValidationResult:
        if request.mode != ValidationMode.FULL:
            # Basic and structural checks are the same for both parents and must not open the file.
            return VectorFileValidator.validate(self, request)
        try:
            try:
                self._declared = self._read_declarations(request)
            except Exception:
                self._declared = []  # no vector layer Fiona can open: validated as raster
            if self.has_vector_layers(request):
                return VectorFileValidator.validate(self, request)
            else:
                return RasterFileValidator.validate(self, request)
        finally:
            self._declared = None
