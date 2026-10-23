"""Test cases for GPX Validator using real data files."""
import pytest
from pathlib import Path

from format_validator.validators.eo.gpx_validator import GPXValidator
from format_validator import ValidationMode, FileInput, FormatIdentifier, ValidationRequest, ValidationResult, Cause, ValidationStatus
from format_validator.validators import EOMetadata
from shapely import GeometryType
from test.fixtures import gpx_input, geojson_input, kml_input, wgs84_crs, mercator_crs, nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def gpx_validator():
    """GPX validator instance."""
    return GPXValidator()


# ========== Test get_extensions() Method ==========

class TestGPXValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, gpx_validator):
        """Test that .gpx extension is returned."""
        extensions = gpx_validator.get_extensions()
        assert '.gpx' in extensions


# ========== Test assert_extension() Method ==========

class TestGPXValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, gpx_validator, gpx_input):
        """Test extension validation passes for .gpx file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.BASIC,
        )
        result: ValidationResult = gpx_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, gpx_validator, geojson_input, kml_input):
        """Test extension validation fails for non-.gpx files."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC,
        )
        result = gpx_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=kml_input,
            mode=ValidationMode.BASIC,
        )
        result = gpx_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestGPXValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, gpx_validator, gpx_input):
        """Test file existence passes for existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = gpx_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, gpx_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = gpx_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestGPXValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, gpx_validator, gpx_input):
        """Test opening a real GPX file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.FULL,
        )
        result = gpx_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, gpx_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
        )
        result = gpx_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestGPXValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, gpx_validator, gpx_input, wgs84_crs):
        """Test CRS extraction returns WGS84 CRS (GPX default)."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        crs = gpx_validator.get_crs(request)
        assert crs is not None
        assert crs == wgs84_crs

    def test_get_crs_none(self, gpx_validator, nonexistent_input):
        """Test CRS extraction returns None for non-GPX file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
        )
        crs = gpx_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestGPXValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, gpx_validator, gpx_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        result = gpx_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, gpx_validator, gpx_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=mercator_crs),
        )
        result = gpx_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, gpx_validator, gpx_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.FULL,
        )
        result = gpx_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, gpx_validator, nonexistent_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        result = gpx_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestGPXValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, gpx_validator, gpx_input):
        """Test BASIC mode passes for valid .gpx file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.BASIC,
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, gpx_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC,
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestGPXValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, gpx_validator, gpx_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, gpx_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, gpx_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.gpx'))
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL,
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestGPXValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, gpx_validator, gpx_input, wgs84_crs):
        """Test FULL mode passes for valid GPX file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=gpx_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.LINESTRING),
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, gpx_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POLYGON),
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, gpx_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GPX,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs, geometry_type=GeometryType.POLYGON),
        )
        result = gpx_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())

