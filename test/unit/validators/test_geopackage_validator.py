"""Test cases for GeoPackage Validator using real data files."""
import pytest
from pathlib import Path
from pyproj import CRS
from shapely import GeometryType

from eo_format_validator.validators.geopackage_validator import GeoPackageValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


@pytest.fixture
def geopackage_validator():
    """Create the actual GeoPackage validator instance (not a mock)."""
    return GeoPackageValidator()


@pytest.fixture
def italian_cities_gpkg():
    """Use the real GeoPackage file (vector)."""
    return DATA_DIR / "Italian_cities.gpkg"


@pytest.fixture
def st_louis_gpkg():
    """Use the real GeoPackage file."""
    return DATA_DIR / "StLouis.gpkg"


@pytest.fixture
def test_raster_only_gpkg():
    """Use the real raster-only GeoPackage file."""
    return DATA_DIR / "test_raster_only_full.gpkg"


@pytest.fixture
def validation_request(italian_cities_gpkg):
    """Create a validation request using a real GeoPackage."""
    return EOValidationRequest(
        format_identifier="format_4107",
        actual_file=FileInput(path=italian_cities_gpkg),
        mode=ValidationMode.STRUCTURAL
    )


class TestGeoPackageValidatorExtension:
    """Test GeoPackage validator extension handling."""

    def test_get_extensions(self, geopackage_validator):
        """Test that GeoPackage validator accepts gpkg extension."""
        extensions = geopackage_validator.get_extensions()
        assert '.gpkg' in extensions
        assert len(extensions) == 1


class TestGeoPackageValidatorAssertExists:
    """Test GeoPackage validator file existence checks."""

    def test_assert_exists_passes(self, geopackage_validator, italian_cities_gpkg):
        """Test file existence passes for real GeoPackage files."""
        request = EOValidationRequest(
            format_identifier="format_4107",
            actual_file=FileInput(path=italian_cities_gpkg),
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.assert_exists(request)
        assert result.status.value == "success"

    def test_assert_exists_fails(self, geopackage_validator):
        """Test file existence fails for non-existent files."""
        request = EOValidationRequest(
            format_identifier="format_4107",
            actual_file=FileInput(path=Path("/nonexistent/file.gpkg")),
            mode=ValidationMode.STRUCTURAL
        )
        result = geopackage_validator.assert_exists(request)
        assert result.status.value == "failure"


class TestGeoPackageValidatorGpkgTables:
    """Test GeoPackage validator table checking with real files."""

    def test_assert_gpkg_tables_on_italian_cities(self, geopackage_validator, italian_cities_gpkg):
        """Test that a real GeoPackage has the required tables."""
        request = EOValidationRequest(
            format_identifier="format_4107",
            actual_file=FileInput(path=italian_cities_gpkg),
            mode=ValidationMode.FULL
        )
        result = GeoPackageValidator.assert_gpkg_tables(request)
        assert result.status.value == "success"


class TestGeoPackageValidatorHasVectorLayers:
    """Test GeoPackage validator vector layer detection."""

    def test_has_vector_layers_true(self, geopackage_validator, italian_cities_gpkg):
        """Test that Italian_cities.gpkg has vector layers."""
        request = EOValidationRequest(
            format_identifier="format_4107",
            actual_file=FileInput(path=italian_cities_gpkg),
            mode=ValidationMode.STRUCTURAL
        )
        assert geopackage_validator.has_vector_layers(request) is True

    def test_has_vector_layers_false_for_raster(self, geopackage_validator, test_raster_only_gpkg):
        """Test that a raster-only GeoPackage has no vector layers."""
        request = EOValidationRequest(
            format_identifier="format_4107",
            actual_file=FileInput(path=test_raster_only_gpkg),
            mode=ValidationMode.STRUCTURAL
        )
        assert geopackage_validator.has_vector_layers(request) is False


class TestGeoPackageValidatorFullValidation:
    """Test GeoPackage validator full validation workflow."""

    def test_validate_structural_with_italian_cities(self, geopackage_validator, validation_request):
        """Test structural validation with a real GeoPackage."""
        result = geopackage_validator.validate(validation_request)
        assert result.status.value == "success"

    def test_validate_full_with_italian_cities(self, geopackage_validator, italian_cities_gpkg):
        """Test full validation with a real GeoPackage."""
        request = EOValidationRequest(
            format_identifier="format_4107",
            actual_file=FileInput(path=italian_cities_gpkg),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        result = geopackage_validator.validate(request)
        assert result.status.value == "success"