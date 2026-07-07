"""Test cases for GML Validator using real data files."""
from pyproj import CRS
import pytest
from pathlib import Path

from eo_format_validator.validators.gml_validator import GMLValidator
from eo_format_validator import ValidationMode, FileInput
from shapely import GeometryType
from eo_format_validator.validators import EOValidationRequest
from eo_format_validator.model.validation_result import ValidationStatus
from eo_format_validator.model import ValidationResult, Error, Cause
from fixtures import gml_input, geojson_input, gpx_input, wgs84_crs, mercator_crs, nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def gml_validator():
    """GML validator instance."""
    return GMLValidator()

@pytest.fixture
def epsg_25832_crs():
    """CRS for EPSG:25832."""
    return CRS.from_epsg(25832)

# ========== Test get_extensions() Method ==========

class TestGMLValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, gml_validator):
        """Test that .gml extension is returned."""
        extensions = gml_validator.get_extensions()
        assert '.gml' in extensions


# ========== Test assert_extension() Method ==========

class TestGMLValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, gml_validator, gml_input):
        """Test extension validation passes for .gml file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.BASIC
        )
        result = gml_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, gml_validator, geojson_input, gpx_input):
        """Test extension validation fails for non-.gml files."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = gml_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gpx_input,
            mode=ValidationMode.BASIC
        )
        result = gml_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestGMLValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, gml_validator, gml_input):
        """Test file existence passes for existing file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = gml_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, gml_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = gml_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestGMLValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, gml_validator, gml_input):
        """Test opening a real GML file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.FULL
        )
        result = gml_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, gml_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = gml_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestGMLValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, gml_validator, gml_input):
        """Test CRS extraction returns a CRS."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.CRS
        )
        crs = gml_validator.get_crs(request)
        assert crs is not None

    def test_get_crs_none(self, gml_validator, nonexistent_input):
        """Test CRS extraction returns None for non-GML file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=nonexistent_input,
            mode=ValidationMode.CRS
        )
        crs = gml_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestGMLValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, gml_validator, gml_input,epsg_25832_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.CRS,
            crs=epsg_25832_crs
        )
        result = gml_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, gml_validator, gml_input,wgs84_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = gml_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, gml_validator, gml_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.CRS
        )
        result = gml_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, gml_validator, nonexistent_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=nonexistent_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = gml_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test validate() with BASIC Mode ==========

class TestGMLValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, gml_validator, gml_input):
        """Test BASIC mode passes for valid .gml file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.BASIC
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, gml_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestGMLValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, gml_validator, gml_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, gml_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, gml_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.gml'))
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestGMLValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, gml_validator, gml_input,epsg_25832_crs):
        """Test FULL mode passes for valid GML file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.FULL,
            crs=epsg_25832_crs,
            geometry_type=GeometryType.LINESTRING
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, gml_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_wrong_geometry_type(self, gml_validator, gml_input, wgs84_crs):
        """Test FULL mode fails for wrong geometry type."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POINT
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE

    def test_validate_full_negative_nonexistent(self, gml_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestGMLValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_no_expected(self, gml_validator, gml_input):
        """Test CRS mode passes when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.CRS
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive(self, gml_validator, gml_input, epsg_25832_crs):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.CRS,
            crs=epsg_25832_crs
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, gml_validator, gml_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=gml_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, gml_validator, nonexistent_input, wgs84_crs):
        """Test CRS mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=nonexistent_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = gml_validator.validate(request)
        assert result.status == ValidationStatus.UNCERTAIN