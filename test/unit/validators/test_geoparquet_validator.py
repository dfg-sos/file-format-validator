"""Test cases for GeoParquet Validator using real data files."""
import pytest
from pathlib import Path
from pyproj import CRS
from shapely import GeometryType

from eo_format_validator.validators.geoparquet_validator import GeoParquetValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


@pytest.fixture
def geoparquet_validator():
    """Create the actual GeoParquet validator instance."""
    return GeoParquetValidator()


@pytest.fixture
def hannover_geoparquet():
    """Use the real GeoParquet file."""
    return DATA_DIR / "hannover_buildings.geoparquet"


@pytest.fixture
def example_parquet():
    """Use the real parquet file."""
    return DATA_DIR / "example.parquet"


@pytest.fixture
def validation_request(hannover_geoparquet):
    """Create a validation request for GeoParquet."""
    return EOValidationRequest(
        format_identifier="format_4108",
        actual_file=FileInput(path=hannover_geoparquet),
        mode=ValidationMode.STRUCTURAL
    )


class TestGeoParquetValidatorExtension:
    """Test GeoParquet validator extension handling."""

    def test_get_extensions(self, geoparquet_validator):
        """Test that GeoParquet validator accepts parquet extensions."""
        extensions = geoparquet_validator.get_extensions()
        assert '.parquet' in extensions
        assert '.geoparquet' in extensions
        assert len(extensions) == 2


class TestGeoParquetValidatorAssertExists:
    """Test GeoParquet validator file existence checks."""

    def test_assert_exists_passes(self, geoparquet_validator, hannover_geoparquet):
        """Test file existence passes for real files."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=hannover_geoparquet),
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.assert_exists(request)
        assert result.status.value == "success"

    def test_assert_exists_fails(self, geoparquet_validator):
        """Test file existence fails for non-existent files."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=Path("/nonexistent/file.parquet")),
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.assert_exists(request)
        assert result.status.value == "failure"


class TestGeoParquetValidatorAssertCanOpen:
    """Test GeoParquet validator open/assertion functionality with real files."""

    def test_assert_can_open_with_hannover(self, geoparquet_validator, hannover_geoparquet):
        """Test opening a real GeoParquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=hannover_geoparquet),
            mode=ValidationMode.FULL
        )
        result = geoparquet_validator.assert_can_open(request)
        assert result.status.value == "success"

    def test_assert_can_open_with_example_parquet(self, geoparquet_validator, example_parquet):
        """Test opening a plain Parquet file (may or may not have geo metadata)."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=example_parquet),
            mode=ValidationMode.FULL
        )
        result = geoparquet_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestGeoParquetValidatorCRS:
    """Test GeoParquet validator CRS functionality."""

    def test_get_crs_from_hannover(self, geoparquet_validator, hannover_geoparquet):
        """Test CRS extraction from a real GeoParquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=hannover_geoparquet),
            mode=ValidationMode.CRS
        )
        crs = geoparquet_validator.get_crs(request)
        # Hannover buildings should have a defined CRS
        assert crs is not None


class TestGeoParquetValidatorGeometryType:
    """Test GeoParquet validator geometry type functionality."""

    def test_assert_geometry_type_from_hannover(self, geoparquet_validator, hannover_geoparquet):
        """Test geometry type detection from a real GeoParquet file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=hannover_geoparquet),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POLYGON
        )
        result = geoparquet_validator.assert_geometry_type(request)
        assert result.status.value == "success"


class TestGeoParquetValidatorFullValidation:
    """Test GeoParquet validator full validation workflow."""

    def test_validate_structural_mode(self, geoparquet_validator, hannover_geoparquet):
        """Test validation in structural mode with a real file."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=hannover_geoparquet),
            mode=ValidationMode.STRUCTURAL
        )
        result = geoparquet_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full_mode(self, geoparquet_validator, hannover_geoparquet):
        """Test validation in full mode."""
        request = EOValidationRequest(
            format_identifier="format_4108",
            actual_file=FileInput(path=hannover_geoparquet),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POLYGON
        )
        result = geoparquet_validator.validate(request)
        assert result.status.value == "success"