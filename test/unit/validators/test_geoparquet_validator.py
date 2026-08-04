"""Test cases for GeoParquet Validator using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.eo.geoparquet_validator import GeoParquetValidator
from eo_format_validator import ValidationMode, FileInput
from shapely import GeometryType
from eo_format_validator.validators import EOValidationRequest
from eo_format_validator.model.validation_result import ValidationStatus
from eo_format_validator.model import ValidationResult, Error, Cause
from fixtures import geoparquet_input, example_parquet_input, geojson_input, wgs84_crs, mercator_crs, nonexistent_input


# ========== Local Fixtures ==========

@pytest.fixture
def geoparquet_validator():
    """GeoParquet validator instance."""
    return GeoParquetValidator()


# ========== Test get_extensions() Method ==========

class TestGeoParquetValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, geoparquet_validator):
        """Test that .parquet and .geoparquet extensions are returned."""
        extensions = geoparquet_validator.get_extensions()
        assert '.parquet' in extensions
        assert '.geoparquet' in extensions


# ========== Test assert_extension() Method ==========

class TestGeoParquetValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, geoparquet_validator, geoparquet_input):
        """Test extension validation passes for .parquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.BASIC
        )
        result = geoparquet_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, geoparquet_validator, geojson_input):
        """Test extension validation fails for non-.parquet files."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = geoparquet_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test assert_exists() Method ==========

class TestGeoParquetValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, geoparquet_validator, geoparquet_input):
        """Test file existence passes for existing file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, geoparquet_validator, nonexistent_input):
        """Test file existence fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestGeoParquetValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, geoparquet_validator, geoparquet_input):
        """Test opening a real GeoParquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.FULL
        )
        result = geoparquet_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_with_plain_parquet(self, geoparquet_validator, example_parquet_input):
        """Test opening a plain Parquet file (may not have geo metadata)."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=example_parquet_input,
            mode=ValidationMode.FULL
        )
        result = geoparquet_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, geoparquet_validator, geojson_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.FULL
        )
        result = geoparquet_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestGeoParquetValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, geoparquet_validator, geoparquet_input, wgs84_crs):
        """Test CRS extraction returns the expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = geoparquet_validator.get_crs(request)
        assert crs is not None

    def test_get_crs_none(self, geoparquet_validator, geojson_input):
        """Test CRS extraction returns None for non-GeoParquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.CRS
        )
        crs = geoparquet_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestGeoParquetValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, geoparquet_validator, geoparquet_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geoparquet_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, geoparquet_validator, geoparquet_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = geoparquet_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, geoparquet_validator, geoparquet_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.CRS
        )
        result = geoparquet_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_no_actual(self, geoparquet_validator, geojson_input, wgs84_crs):
        """Test CRS validation is uncertain when CRS could not be read from file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geoparquet_validator.assert_crs(request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert any(warn.cause == Cause.MISSING_METADATA for warn in result.warnings())


# ========== Test assert_geometry_type() Method ==========

class TestGeoParquetValidatorAssertGeometryType:
    """Test assert_geometry_type() method."""

    def test_assert_geometry_type_passes(self, geoparquet_validator, geoparquet_input):
        """Test geometry type validation passes with matching expected type."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POLYGON
        )
        result = geoparquet_validator.assert_geometry_type(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_geometry_type_fails(self, geoparquet_validator, geoparquet_input):
        """Test geometry type validation fails with mismatching expected type."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        result = geoparquet_validator.assert_geometry_type(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())


# ========== Test validate() with BASIC Mode ==========

class TestGeoParquetValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, geoparquet_validator, geoparquet_input):
        """Test BASIC mode passes for valid .parquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.BASIC
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, geoparquet_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestGeoParquetValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, geoparquet_validator, geoparquet_input):
        """Test STRUCTURAL mode passes for valid existing file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, geoparquet_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, geoparquet_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=nonexistent_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())
        
        valid_extension_nonexistent_file = FileInput(path=nonexistent_input.path.with_suffix('.parquet'))
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=valid_extension_nonexistent_file,
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestGeoParquetValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, geoparquet_validator, geoparquet_input, wgs84_crs):
        """Test FULL mode passes for valid GeoParquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, geoparquet_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, geoparquet_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=nonexistent_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestGeoParquetValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_no_expected(self, geoparquet_validator, geoparquet_input):
        """Test CRS mode passes when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.CRS
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive(self, geoparquet_validator, geoparquet_input, wgs84_crs):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, geoparquet_validator, geoparquet_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geoparquet_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, geoparquet_validator, geojson_input, wgs84_crs):
        """Test CRS mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = geoparquet_validator.validate(request)
        assert result.status == ValidationStatus.UNCERTAIN