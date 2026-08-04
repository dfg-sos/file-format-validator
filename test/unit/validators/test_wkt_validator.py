"""Test cases for WKT Validator using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.eo.wkt_validator import WKTValidator
from eo_format_validator import ValidationMode, FileInput
from shapely import GeometryType
from eo_format_validator.validators import EOValidationRequest
from eo_format_validator.model.validation_result import ValidationStatus
from eo_format_validator.model import ValidationResult, Error, Cause
from fixtures import wkt_input, wkt_sparql_input, geojson_input, wgs84_crs, mercator_crs, nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def wkt_validator():
    """WKT validator instance."""
    return WKTValidator()


# ========== Test get_extensions() Method ==========

class TestWKTValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, wkt_validator):
        """Test that .wkt and .txt extensions are returned."""
        extensions = wkt_validator.get_extensions()
        assert '.wkt' in extensions
        assert '.txt' in extensions


# ========== Test assert_extension() Method ==========

class TestWKTValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, wkt_validator, wkt_input):
        """Test extension validation passes for .wkt file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.BASIC
        )
        result = wkt_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_valid_txt(self, wkt_validator, wkt_sparql_input):
        """Test extension validation passes for .txt file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_sparql_input,
            mode=ValidationMode.BASIC
        )
        result = wkt_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, wkt_validator, geojson_input):
        """Test extension validation fails for non-.wkt files."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = wkt_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestWKTValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, wkt_validator, wkt_input):
        """Test file existence passes for existing file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = wkt_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, wkt_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = wkt_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestWKTValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes_ewkt(self, wkt_validator, wkt_input):
        """Test opening a real EWKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.FULL
        )
        result = wkt_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_passes_sparql_wkt(self, wkt_validator, wkt_sparql_input):
        """Test opening a real GeoSPARQL WKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_sparql_input,
            mode=ValidationMode.FULL
        )
        result = wkt_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, wkt_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = wkt_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestWKTValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs_from_ewkt(self, wkt_validator, wkt_input, wgs84_crs):
        """Test CRS extraction from EWKT file (SRID=4326)."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = wkt_validator.get_crs(request)
        assert crs is not None
        assert crs == wgs84_crs

    def test_get_crs_from_sparql_wkt(self, wkt_validator, wkt_sparql_input):
        """Test CRS extraction from GeoSPARQL WKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_sparql_input,
            mode=ValidationMode.CRS
        )
        crs = wkt_validator.get_crs(request)
        assert crs is not None

    def test_get_crs_none(self, wkt_validator, geojson_input):
        """Test CRS extraction returns None for non-WKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=geojson_input,
            mode=ValidationMode.CRS
        )
        crs = wkt_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestWKTValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, wkt_validator, wkt_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = wkt_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, wkt_validator, wkt_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = wkt_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, wkt_validator, wkt_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.CRS
        )
        result = wkt_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS


# ========== Test assert_geometry_type() Method ==========

class TestWKTValidatorAssertGeometryType:
    """Test assert_geometry_type() method."""

    def test_assert_geometry_type_point_from_ewkt(self, wkt_validator, wkt_input):
        """Test detecting POINT geometry from EWKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        result = wkt_validator.assert_geometry_type(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_geometry_type_geometrycollection_from_sparql(self, wkt_validator, wkt_sparql_input):
        """Test detecting GEOMETRYCOLLECTION from GeoSPARQL WKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_sparql_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.GEOMETRYCOLLECTION
        )
        result = wkt_validator.assert_geometry_type(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_geometry_type_fails(self, wkt_validator, wkt_input):
        """Test geometry type validation fails with mismatching expected type."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.GEOMETRYCOLLECTION  # This type is not in the file
        )
        result = wkt_validator.assert_geometry_type(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())


# ========== Test validate() with BASIC Mode ==========

class TestWKTValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, wkt_validator, wkt_input):
        """Test BASIC mode passes for valid .wkt file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.BASIC
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, wkt_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestWKTValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, wkt_validator, wkt_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, wkt_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, wkt_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.wkt'))
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestWKTValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive_ewkt(self, wkt_validator, wkt_input, wgs84_crs):
        """Test FULL mode passes for valid EWKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POINT
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_positive_sparql_wkt(self, wkt_validator, wkt_sparql_input):
        """Test FULL mode passes for valid GeoSPARQL WKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_sparql_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.GEOMETRYCOLLECTION
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, wkt_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POINT
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, wkt_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POINT
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestWKTValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_no_expected(self, wkt_validator, wkt_input):
        """Test CRS mode passes when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.CRS
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive(self, wkt_validator, wkt_input, wgs84_crs):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, wkt_validator, wkt_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=wkt_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, wkt_validator, geojson_input, wgs84_crs):
        """Test CRS mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = wkt_validator.validate(request)
        assert result.status == ValidationStatus.UNCERTAIN