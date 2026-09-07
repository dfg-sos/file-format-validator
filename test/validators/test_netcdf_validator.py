"""Test cases for NetCDF Validator using real data files."""
import pytest
from pathlib import Path

from format_validator.validators.eo.netcdf_validator import NetCDFValidator
from format_validator import ValidationMode, FileInput, FormatIdentifier, ValidationRequest, EOMetadata, ValidationResult, Cause, ValidationStatus
from test.fixtures import netcdf_input, geojson_input, geopackage_input, wgs84_crs, mercator_crs, nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def netcdf_validator():
    """NetCDF validator instance."""
    return NetCDFValidator()


# ========== Test get_extensions() Method ==========

class TestNetCDFValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, netcdf_validator):
        """Test that .nc extension is returned."""
        extensions = netcdf_validator.get_extensions()
        assert '.nc' in extensions


# ========== Test assert_extension() Method ==========

class TestNetCDFValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, netcdf_validator, netcdf_input):
        """Test extension validation passes for .nc file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.BASIC,
        )
        result: ValidationResult = netcdf_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, netcdf_validator, geojson_input, geopackage_input):
        """Test extension validation fails for non-.nc files."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC,
        )
        result = netcdf_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geopackage_input,
            mode=ValidationMode.BASIC,
        )
        result = netcdf_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestNetCDFValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, netcdf_validator, netcdf_input):
        """Test file existence passes for existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = netcdf_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, netcdf_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = netcdf_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestNetCDFValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, netcdf_validator, netcdf_input):
        """Test opening a real NetCDF file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.FULL,
        )
        result = netcdf_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, netcdf_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
        )
        result = netcdf_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestNetCDFValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, netcdf_validator, netcdf_input):
        """Test CRS extraction returns a CRS."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.FULL,
        )
        crs = netcdf_validator.get_crs(request)
        assert crs is not None

    def test_get_crs_none(self, netcdf_validator, geojson_input):
        """Test CRS extraction returns None for non-NetCDF file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
        )
        crs = netcdf_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestNetCDFValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_no_expected(self, netcdf_validator, netcdf_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.FULL,
        )
        result = netcdf_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, netcdf_validator, geojson_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            metadata=EOMetadata(crs=wgs84_crs),
        )
        result = netcdf_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestNetCDFValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, netcdf_validator, netcdf_input):
        """Test BASIC mode passes for valid .nc file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.BASIC,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, netcdf_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geojson_input,
            mode=ValidationMode.BASIC,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestNetCDFValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, netcdf_validator, netcdf_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, netcdf_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, netcdf_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.nc'))
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestNetCDFValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open)."""

    def test_validate_full_positive(self, netcdf_validator, netcdf_input):
        """Test FULL mode passes for valid NetCDF file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=netcdf_input,
            mode=ValidationMode.FULL,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, netcdf_validator, geojson_input):
        """Test FULL mode fails for wrong file format."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, netcdf_validator, nonexistent_input):
        """Test FULL mode fails for non-existent file."""
        request = ValidationRequest(
            format_identifier=FormatIdentifier.NETCDF,
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
        )
        result = netcdf_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())

