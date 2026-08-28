"""Test cases for GeoPackage Validator using real data files."""
import pytest
from pathlib import Path

from format_validator.validators.eo.geopackage_validator import GeoPackageValidator
from format_validator import ValidationMode, FileInput
from shapely import GeometryType
from format_validator.model.format_identifier import FormatIdentifier
from format_validator.validators import EOValidationRequest
from format_validator.model.validation_result import ValidationStatus
from format_validator.model import ValidationResult, Error, Cause
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
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.BASIC
        )
        result = geopackage_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, geopackage_validator, geojson_input, gpx_input):
        """Test extension validation fails for non-.gpkg files."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = geopackage_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=gpx_input,
            mode=ValidationMode.BASIC
        )
        result = geopackage_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestGeoPackageValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, geopackage_validator, geopackage_input):
        """Test file existence passes for existing file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, geopackage_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestGeoPackageValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, geopackage_validator, geopackage_input):
        """Test opening a real GeoPackage file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL
        )
        result = geopackage_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, geopackage_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = geopackage_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestGeoPackageValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test CRS extraction returns the expected CRS."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = geopackage_validator.get_crs(request)
        assert crs is not None
        assert crs == wgs84_crs

    def test_get_crs_none(self, geopackage_validator, nonexistent_input, wgs84_crs):
        """Test CRS extraction returns None for non-GeoPackage file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = geopackage_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestGeoPackageValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, geopackage_validator, geopackage_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, geopackage_validator, geopackage_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.CRS
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, geopackage_validator, nonexistent_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geopackage_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestGeoPackageValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, geopackage_validator, geopackage_input):
        """Test BASIC mode passes for valid .gpkg file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.BASIC
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, geopackage_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestGeoPackageValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, geopackage_validator, geopackage_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, geopackage_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, geopackage_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.gpkg'))
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestGeoPackageValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test FULL mode passes for valid GeoPackage file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_geometry_type(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test FULL mode fails for wrong geometry type."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POINT
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE

    def test_validate_full_negative_wrong_format(self, geopackage_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, geopackage_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestGeoPackageValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_no_expected(self, geopackage_validator, geopackage_input):
        """Test CRS mode passes when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.CRS
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive(self, geopackage_validator, geopackage_input, wgs84_crs):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, geopackage_validator, geopackage_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=geopackage_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = geopackage_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, geopackage_validator, wkt_input, wgs84_crs):
        """Test CRS mode with compatible CRS from wrong format.
        """
        request = EOValidationRequest(
            format_identifier=FormatIdentifier.GEOPACKAGE,
            actual_file=wkt_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geopackage_validator.validate(request)
