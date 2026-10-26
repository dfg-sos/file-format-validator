"""Test cases for GeoPackage Validator using real data files."""
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon

from format_validator.validators.eo.geopackage_validator import GeoPackageValidator
from format_validator.validators.eo.vector_file_validator import MAX_FEATURES_TO_INSPECT
from format_validator import ValidationMode, FileInput, FormatIdentifier, ValidationRequest, ValidationResult, Cause, ValidationStatus
from format_validator.validators import EOMetadata
from shapely import GeometryType
from test.fixtures import geopackage_input, geopackage_raster_input, geojson_input, gpx_input, wgs84_crs, mercator_crs, nonexistent_input,wkt_input


# ========== Local Fixtures ==========

@pytest.fixture
def geopackage_validator():
    """GeoPackage validator instance."""
    return GeoPackageValidator()


# ========== Test get_extensions() Method ==========

class TestGeoPackageValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, geopackage_validator):
        """Test that .gpkg extension is returned."""
        extensions = geopackage_validator.get_extensions()
        assert '.gpkg' in extensions


# ========== Test assert_extension() Method ==========

class TestGeoPackageValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, geopackage_validator, geopackage_input):
        """Test extension validation passes for .gpkg file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.BASIC,
        )
        result: ValidationResult = geopackage_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, geopackage_validator, geojson_input, gpx_input):
        """Test extension validation fails for non-.gpkg files."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC,
        )
        result = geopackage_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=gpx_input,
            mode=ValidationMode.BASIC,
        )
        result = geopackage_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestGeoPackageValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, geopackage_validator, geopackage_input):
        """Test file existence passes for existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = geopackage_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, geopackage_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = geopackage_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestGeoPackageValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, geopackage_validator, geopackage_input):
        """Test opening a real GeoPackage file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
        )
        result = geopackage_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, geopackage_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
        )
        result = geopackage_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestGeoPackageValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test CRS extraction returns the expected CRS."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        crs = geopackage_validator.get_crs(request)
        assert crs is not None
        assert crs == wgs84_crs

    def test_get_crs_none(self, geopackage_validator, nonexistent_input, wgs84_crs):
        """Test CRS extraction returns None for non-GeoPackage file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        crs = geopackage_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestGeoPackageValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, geopackage_validator, geopackage_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=mercator_crs),
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, geopackage_validator, geopackage_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, geopackage_validator, nonexistent_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestGeoPackageValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, geopackage_validator, geopackage_input):
        """Test BASIC mode passes for valid .gpkg file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.BASIC,
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, geopackage_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC,
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestGeoPackageValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, geopackage_validator, geopackage_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, geopackage_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, geopackage_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.gpkg'))
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL,
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestGeoPackageValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test FULL mode passes for valid GeoPackage file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POLYGON),
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_geometry_type(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test FULL mode fails for wrong geometry type."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POINT),
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE

    def test_validate_full_negative_wrong_format(self, geopackage_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POLYGON),
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, geopackage_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POLYGON),
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())



# ========== Regression Tests ==========

def _write_gpkg(path, geometries):
    gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326").to_file(path, driver="GPKG")


class TestGeoPackageValidatorRegressions:
    """Reading only in FULL mode, no reads cached across calls, optional tables not reported as warning."""

    @pytest.mark.parametrize("mode", [ValidationMode.BASIC, ValidationMode.STRUCTURAL])
    def test_basic_and_structural_do_not_read_file(self, geopackage_validator, geopackage_input, mode):
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=mode,
        )
        module = "format_validator.validators.eo.geopackage_validator"
        with patch(f"{module}.fiona.open") as fiona_open, patch(f"{module}.fiona.listlayers") as listlayers, \
                patch(f"{module}.sqlite3.connect") as connect:
            result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS
        fiona_open.assert_not_called()
        listlayers.assert_not_called()
        connect.assert_not_called()

    def test_replaced_file_at_same_path_gives_new_result(self, geopackage_validator, tmp_path, wgs84_crs):
        path = tmp_path / "stale.gpkg"
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=FileInput(path=path),
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POLYGON),
        )
        _write_gpkg(path, [LineString([(0, 0), (1, 1)])])
        assert geopackage_validator.validate(request).status == ValidationStatus.FAILURE

        path.unlink()
        _write_gpkg(path, [Polygon([(0, 0), (1, 0), (1, 1)])])
        assert geopackage_validator.validate(request).status == ValidationStatus.SUCCESS
        assert GeoPackageValidator().validate(request).status == ValidationStatus.SUCCESS

    def test_full_reads_no_features_of_declared_layers(self, geopackage_validator, tmp_path, wgs84_crs):
        path = tmp_path / "declared.gpkg"
        _write_gpkg(path, [LineString([(0, 0), (1, 1)])])
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=FileInput(path=path),
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.LINESTRING),
        )
        with patch("format_validator.validators.eo.geopackage_validator.sample_geometry_types") as sample:
            result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS
        sample.assert_not_called()

    def test_generic_geometry_layer_is_sampled(self, geopackage_validator, tmp_path, wgs84_crs):
        """A layer declaring GEOMETRY may hold anything, so its features decide."""
        path = tmp_path / "generic.gpkg"
        gpd.GeoDataFrame(geometry=[Point(0, 0), LineString([(0, 0), (1, 1)])], crs="EPSG:4326").to_file(
            path, driver="GPKG", geometry_type="Unknown"
        )
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=FileInput(path=path),
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POLYGON),
        )
        assert set(geopackage_validator.get_geometry_types(request)) == {GeometryType.POINT, GeometryType.LINESTRING}
        assert geopackage_validator.validate(request).status == ValidationStatus.FAILURE

    def test_gdal_default_gpkg_without_metadata_tables_is_success_with_info(self, geopackage_validator, tmp_path, wgs84_crs):
        path = tmp_path / "gdal_default.gpkg"
        _write_gpkg(path, [Point(0, 0)])
        with sqlite3.connect(path) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "gpkg_metadata" not in tables

        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=FileInput(path=path),
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POINT),
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS
        assert any("optional tables" in info.message for info in result.infos())

    def test_generic_geometry_layer_samples_only_first_features(self, geopackage_validator, tmp_path):
        path = tmp_path / "generic_large.gpkg"
        geometries = [Point(i, 0) for i in range(MAX_FEATURES_TO_INSPECT)] + [LineString([(0, 0), (1, 1)])]
        gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326").to_file(path, driver="GPKG", geometry_type="Unknown")
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=FileInput(path=path),
            mode=ValidationMode.FULL,
        )
        assert geopackage_validator.get_geometry_types(request) == [GeometryType.POINT]

    def test_path_with_uri_characters(self, geopackage_validator, tmp_path, wgs84_crs):
        """'#', '?' and '%' in the path must not cut the sqlite URI short and create another database."""
        path = tmp_path / "a#b?c%20.gpkg"
        _write_gpkg(path, [Point(0, 0)])
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=FileInput(path=path),
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POINT),
        )
        assert geopackage_validator.validate(request).status == ValidationStatus.SUCCESS
        assert list(tmp_path.iterdir()) == [path]

    def test_raster_only_full(self, geopackage_validator, geopackage_raster_input, wgs84_crs):
        """Fiona cannot open a GeoPackage without vector layers, so it is validated as a raster."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_raster_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS
        assert geopackage_validator.get_crs(request) == wgs84_crs
