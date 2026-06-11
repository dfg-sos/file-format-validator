"""Test cases for GeoJSON Validator using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.geojson_validator import GeoJSONValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest
from shapely import GeometryType

DATA_DIR = Path("data/geo")


@pytest.fixture
def geojson_validator():
    """Create the actual GeoJSON validator instance."""
    return GeoJSONValidator()


@pytest.fixture
def geojson_de_file():
    """Use the real GeoJSON data file for German states."""
    return DATA_DIR / "geojson_de.json"


@pytest.fixture
def validation_request(geojson_de_file):
    """Create a validation request for STRUCTURAL mode using the real file."""
    return EOValidationRequest(
        format_identifier="format_4106",
        actual_file=FileInput(path=geojson_de_file),
        mode=ValidationMode.STRUCTURAL
    )


class TestGeoJSONValidatorExtension:
    """Test GeoJSON validator extension handling."""

    def test_get_extensions(self, geojson_validator):
        """Test that GeoJSON validator accepts expected extensions."""
        extensions = geojson_validator.get_extensions()
        assert '.geojson' in extensions
        assert '.json' in extensions
        assert len(extensions) == 2

    def test_assert_extension_passes_with_geojson(self, geojson_validator, validation_request):
        """Test extension validation passes for .geojson files."""
        result = geojson_validator.assert_extension(validation_request)
        assert result.status.value == "success"

    def test_assert_extension_fails_with_wrong_extension(self, geojson_validator):
        """Test extension validation fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=FileInput(path=Path("/fake/file.txt")),
            mode=ValidationMode.BASIC
        )
        result = geojson_validator.assert_extension(request)
        assert result.status.value == "failure"
        assert any("extension" in err.message.lower() for err in result.errors())


class TestGeoJSONValidatorExists:
    """Test GeoJSON validator file existence checks."""

    def test_assert_exists_passes_for_real_file(self, geojson_validator, geojson_de_file):
        """Test file existence passes for a real data file."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=FileInput(path=geojson_de_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.assert_exists(request)
        assert result.status.value == "success"

    def test_assert_exists_fails_for_nonexistent_file(self, geojson_validator):
        """Test file existence fails for non-existent files."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=FileInput(path=Path("/nonexistent/file.geojson")),
            mode=ValidationMode.STRUCTURAL
        )
        result = geojson_validator.assert_exists(request)
        assert result.status.value == "failure"
        assert any(cause == Cause.PATH_ERROR for err in result.errors() for cause in [err.cause])


class TestGeoJSONValidatorCRS:
    """Test GeoJSON validator CRS functionality using the real file."""

    def test_get_crs_from_real_file(self, geojson_validator, geojson_de_file):
        """Test CRS extraction from the real GeoJSON file via fiona."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=FileInput(path=geojson_de_file),
            mode=ValidationMode.CRS
        )
        crs = geojson_validator.get_crs(request)
        # The GeoJSON file contains polygon data for German states
        # geojson_de.json typically has no explicit CRS, but fiona defaults to EPSG:4326
        assert crs is not None

    def test_assert_crs_matches(self, geojson_validator, geojson_de_file):
        """Test CRS validation passes when expected CRS matches."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=FileInput(path=geojson_de_file),
            mode=ValidationMode.CRS,
            crs=None
        )
        result = geojson_validator.assert_crs(request)
        # No expected CRS provided -> skip CRS validation
        assert result.status.value == "success"


class TestGeoJSONValidatorFullValidation:
    """Test GeoJSON validator full validation workflow."""

    def test_validate_basic_mode(self, geojson_validator, geojson_de_file):
        """Test validation in basic mode (extension check only)."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=FileInput(path=geojson_de_file),
            mode=ValidationMode.BASIC
        )
        result = geojson_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_structural_mode(self, geojson_validator, validation_request):
        """Test validation in structural mode (extension + existence)."""
        result = geojson_validator.validate(validation_request)
        assert result.status.value == "success"

    def test_validate_full_mode(self, geojson_validator, geojson_de_file):
        """Test validation in full mode (extension + existence + open)."""
        request = EOValidationRequest(
            format_identifier="format_4106",
            actual_file=FileInput(path=geojson_de_file),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POLYGON
        )
        result = geojson_validator.validate(request)
        assert result.status.value == "success"