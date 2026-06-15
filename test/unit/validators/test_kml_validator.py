"""Test cases for KML Validator using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.kml_validator import KMLValidator
from eo_format_validator import ValidationMode, FileInput
from shapely import GeometryType
from eo_format_validator.validators import EOValidationRequest
from eo_format_validator.model.validation_result import ValidationStatus
from eo_format_validator.model import ValidationResult, Error, Cause
from fixtures import kml_input, geojson_input, gpx_input, wgs84_crs, mercator_crs, nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def kml_validator():
    """KML validator instance."""
    return KMLValidator()


# ========== Test get_extensions() Method ==========

class TestKMLValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, kml_validator):
        """Test that .kml extension is returned."""
        extensions = kml_validator.get_extensions()
        assert '.kml' in extensions


# ========== Test assert_extension() Method ==========

class TestKMLValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, kml_validator, kml_input):
        """Test extension validation passes for .kml file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.BASIC
        )
        result = kml_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, kml_validator, geojson_input, gpx_input):
        """Test extension validation fails for non-.kml files."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = kml_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=gpx_input,
            mode=ValidationMode.BASIC
        )
        result = kml_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestKMLValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, kml_validator, kml_input):
        """Test file existence passes for existing file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, kml_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestKMLValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, kml_validator, kml_input):
        """Test opening a real KML file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.FULL
        )
        result = kml_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, kml_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = kml_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestKMLValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, kml_validator, kml_input, wgs84_crs):
        """Test CRS extraction returns WGS84 CRS (KML default)."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = kml_validator.get_crs(request)
        assert crs is not None
        assert crs == wgs84_crs

    def test_get_crs_none(self, kml_validator, geojson_input):
        """Test CRS extraction returns None for non-KML file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.CRS
        )
        crs = kml_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestKMLValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, kml_validator, kml_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = kml_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, kml_validator, kml_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = kml_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, kml_validator, kml_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.CRS
        )
        result = kml_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, kml_validator, geojson_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = kml_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestKMLValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, kml_validator, kml_input):
        """Test BASIC mode passes for valid .kml file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.BASIC
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, kml_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestKMLValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, kml_validator, kml_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, kml_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, kml_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.kml'))
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestKMLValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, kml_validator, kml_input, wgs84_crs):
        """Test FULL mode passes for valid KML file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, kml_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, kml_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestKMLValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_no_expected(self, kml_validator, kml_input):
        """Test CRS mode passes when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.CRS
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive(self, kml_validator, kml_input, wgs84_crs):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, kml_validator, kml_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=kml_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, kml_validator, geojson_input, wgs84_crs):
        """Test CRS mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = kml_validator.validate(request)
        assert result.status == ValidationStatus.UNCERTAIN