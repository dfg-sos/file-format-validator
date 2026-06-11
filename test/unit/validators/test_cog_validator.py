"""Test cases for COG (Cloud Optimized GeoTIFF) Validator using real data files."""
import pytest
from pathlib import Path
from pyproj import CRS

from eo_format_validator.validators.cog_validator import COGValidator
from eo_format_validator import ValidationMode, FileInput
from eo_format_validator.validators import EOValidationRequest
from eo_format_validator.model.validation_result import ValidationStatus
from eo_format_validator.model import ValidationResult, Error, Cause
from fixtures import cog_input, geojson_input, geopackage_input, wgs84_crs,mercator_crs,nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def cog_validator():
    """COG validator instance."""
    return COGValidator()

# ========== Test get_extensions() Method ==========

class TestCOGValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, cog_validator):
        """Test that only .tif and .tiff extensions are returned."""
        extensions = cog_validator.get_extensions()
        assert len(extensions) == 2
        assert set(extensions) == {'.tif', '.tiff'}


# ========== Test assert_extension() Method ==========

class TestCOGValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, cog_validator, cog_input):
        """Test extension validation passes for .tif file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.BASIC
        )
        result = cog_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, cog_validator, geojson_input,geopackage_input):
        """Test extension validation fails for .json file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = cog_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geopackage_input,
            mode=ValidationMode.BASIC
        )
        result = cog_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestCOGValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, cog_validator, cog_input):
        """Test file existence passes for existing file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = cog_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, cog_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = cog_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestCOGValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, cog_validator, cog_input):
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.FULL
        )
        result = cog_validator.assert_can_open(request)
        assert result is not None
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, cog_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = cog_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestCOGValidatorGetCRS:
    def test_get_crs(self, cog_validator, cog_input, wgs84_crs):
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = cog_validator.get_crs(request)
        assert crs is not None
        crs1 = cog_validator.get_crs(request)
        assert crs1 == crs
        assert crs1 == wgs84_crs

    def test_get_crs_none(self, cog_validator, geojson_input,wgs84_crs):
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = cog_validator.get_crs(request)
        assert crs is None

# ========== Test assert_crs() Method ==========

class TestCOGValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, cog_validator, cog_input,wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = cog_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, cog_validator, cog_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = cog_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, cog_validator, cog_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS
        )
        result = cog_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, cog_validator, geojson_input,wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = cog_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestCOGValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, cog_validator, cog_input):
        """Test BASIC mode passes for valid .tif file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.BASIC
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, cog_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========
#TODO refactor tests below:

class TestCOGValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, cog_validator, cog_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, cog_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, cog_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        validExtensionNonExistentFile = FileInput(path=nonexistent_input.path.with_suffix('.tif'))
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=validExtensionNonExistentFile,
            mode=ValidationMode.STRUCTURAL
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestCOGValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open)."""

    def test_validate_full_positive(self, cog_validator, cog_input):
        """Test FULL mode passes for valid COG file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.FULL
        )
        result = cog_validator.validate(request)
        assert result.status in (ValidationStatus.SUCCESS, ValidationStatus.UNCERTAIN)

    def test_validate_full_negative_wrong_format(self, cog_validator, geojson_input):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, cog_validator, nonexistent_input):
        """Test FULL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestCOGValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_positive(self, cog_validator, cog_input):
        """Test CRS mode passes for valid file with CRS."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS
        )
        result = cog_validator.validate(request)
        # No expected CRS provided, should succeed with info message
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive_with_matching_crs(self, cog_validator, cog_input):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS
        )
        actual_crs = cog_validator.get_crs(request)
        matching_request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS,
            crs=actual_crs
        )
        result = cog_validator.validate(matching_request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, cog_validator, cog_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=cog_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, cog_validator, geojson_input, wgs84_crs):
        """Test CRS mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4100",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = cog_validator.validate(request)
        assert result.status == ValidationStatus.UNCERTAIN
        # assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())