"""Test cases for GRIB Validator using real data files."""
import pytest
from pathlib import Path

from format_validator.validators.eo.grib_validator import GRIBValidator
from format_validator import ValidationMode, FileInput, FormatIdentifier, ValidationRequest, EOMetadata, ValidationResult, Cause, ValidationStatus
from test.fixtures import grib_input, nonexistent_input, geopackage_input, wgs84_crs, mercator_crs


# ========== Local Fixtures ==========

@pytest.fixture
def grib_validator():
    """GRIB validator instance."""
    return GRIBValidator()


# ========== Test get_extensions() Method ==========

class TestGRIBValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, grib_validator):
        """Test that .grb and .grib2 extensions are returned."""
        extensions = grib_validator.get_extensions()
        assert '.grb' in extensions


# ========== Test assert_extension() Method ==========

class TestGRIBValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, grib_validator, grib_input):
        """Test extension validation passes for .grb file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.BASIC,
        )
        result: ValidationResult = grib_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, grib_validator, nonexistent_input, geopackage_input):
        """Test extension validation fails for non-.grb files."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.BASIC,
        )
        result = grib_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=geopackage_input,
            mode=ValidationMode.BASIC,
        )
        result = grib_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestGRIBValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, grib_validator, grib_input):
        """Test file existence passes for existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = grib_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, grib_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = grib_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestGRIBValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, grib_validator, grib_input):
        """Test opening a real GRIB file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.FULL,
        )
        result = grib_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, grib_validator, nonexistent_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
        )
        result = grib_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestGRIBValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, grib_validator, grib_input):
        """Test CRS extraction returns a CRS."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.FULL,
        )
        crs = grib_validator.get_crs(request)
        assert crs is not None

    def test_get_crs_none(self, grib_validator, nonexistent_input):
        """Test CRS extraction returns None for non-GRIB file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
        )
        crs = grib_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestGRIBValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_no_expected(self, grib_validator, grib_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.FULL,
        )
        result = grib_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, grib_validator, nonexistent_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        result = grib_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestGRIBValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, grib_validator, grib_input):
        """Test BASIC mode passes for valid .grb file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.BASIC,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, grib_validator, nonexistent_input):
        """Test BASIC mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.BASIC,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestGRIBValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, grib_validator, grib_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, grib_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, grib_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.grb'))
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestGRIBValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open)."""

    def test_validate_full_positive(self, grib_validator, grib_input):
        """Test FULL mode passes for valid GRIB file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=grib_input,
            mode=ValidationMode.FULL,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, grib_validator, nonexistent_input):
        """Test FULL mode fails for wrong file format."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, grib_validator, nonexistent_input):
        """Test FULL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.GRIB,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
        )
        result = grib_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())

