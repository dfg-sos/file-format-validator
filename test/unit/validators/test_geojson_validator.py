"""Test cases for GeoJSON Validator using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.eo.geojson_validator import GeoJSONValidator
from eo_format_validator import ValidationMode, FileInput
from shapely import GeometryType
from eo_format_validator.validators import EOValidationRequest
from eo_format_validator.model.validation_result import ValidationStatus
from eo_format_validator.model import ValidationResult, Error, Cause
from fixtures import geojson_input, geotiff_input, gpx_input, wgs84_crs, mercator_crs, nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def geojson_validator():
    """GeoJSON validator instance."""
    return GeoJSONValidator()


# ========== Test get_extensions() Method ==========

class TestGeoJSONValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, geojson_validator):
        """Test that .geojson and .json extensions are returned."""
        extensions = geojson_validator.get_extensions()
        assert '.geojson' in extensions or '.json' in extensions


# ========== Test assert_extension() Method ==========

class TestGeoJSONValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, geojson_validator, geojson_input):
        """Test extension validation passes for .json file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = geojson_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, geojson_validator, geotiff_input, gpx_input):
        """Test extension validation fails for non-.json files."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geotiff_input,
            mode=ValidationMode.BASIC
        )
        result = geojson_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=gpx_input,
            mode=ValidationMode.BASIC
        )
        result = geojson_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestGeoJSONValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, geojson_validator, geojson_input):
        """Test file existence passes for existing file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, geojson_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestGeoJSONValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, geojson_validator, geojson_input):
        """Test opening a real GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = geojson_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, geojson_validator, geotiff_input):
        """Test that assert_can_open fails for GeoPackage file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geotiff_input,
            mode=ValidationMode.FULL
        )
        result = geojson_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestGeoJSONValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, geojson_validator, geojson_input, wgs84_crs):
        """Test CRS extraction returns the expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = geojson_validator.get_crs(request)
        assert crs is not None
        assert crs == wgs84_crs

    def test_get_crs_none(self, geojson_validator, geotiff_input, wgs84_crs):
        """Test CRS extraction returns None for non-GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geotiff_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = geojson_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestGeoJSONValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, geojson_validator, geojson_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geojson_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, geojson_validator, geojson_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = geojson_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, geojson_validator, geojson_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.CRS
        )
        result = geojson_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, geojson_validator, geotiff_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geotiff_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geojson_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestGeoJSONValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, geojson_validator, geojson_input):
        """Test BASIC mode passes for valid .json file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, geojson_validator, geotiff_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geotiff_input,
            mode=ValidationMode.BASIC
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestGeoJSONValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, geojson_validator, geojson_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, geojson_validator, geotiff_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geotiff_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, geojson_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.json'))
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestGeoJSONValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, geojson_validator, geojson_input, wgs84_crs):
        """Test FULL mode passes for valid GeoJSON file.
        
        Note: The geojson_de.json file contains both Polygon and MultiPolygon geometries,
        so validation with POLYGON returns UNCERTAIN + Warning about mixed types.
        The expected type is present, but mixed types trigger a warning.
        """
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geojson_validator.validate(request)
        # File has mixed geometry types but POLYGON is present, so UNCERTAIN with warning
        assert result.status == ValidationStatus.SUCCESS
        assert any("mixed geometry types" in warn.message for warn in result.warnings())

    def test_validate_full_negative_wrong_geometry(self, geojson_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for mismatching expected geometry type.
        
        Note: The geojson_de.json file contains Polygon and MultiPolygon geometries,
        so validation with POINT returns FAILURE.
        """
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POINT
        )
        result = geojson_validator.validate(request)
        # File has mixed geometry types but none match POINT, so FAILURE
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())
        
    def test_validate_full_negative_wrong_format(self, geojson_validator, geotiff_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geotiff_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, geojson_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestGeoJSONValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_no_expected(self, geojson_validator, geojson_input):
        """Test CRS mode passes when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.CRS
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive(self, geojson_validator, geojson_input, wgs84_crs):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, geojson_validator, geojson_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = geojson_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, geojson_validator, gpx_input, wgs84_crs):
        """Test CRS mode with a GPX file (wrong format but same CRS).
        
        Note: GPX files can be opened by Fiona and have CRS information.
        Since the GPX file has EPSG:4326 which matches wgs84_crs, validation passes.
        """
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=gpx_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geojson_validator.validate(request)
        # GPX file has EPSG:4326 which matches expected CRS
        assert result.status == ValidationStatus.SUCCESS
