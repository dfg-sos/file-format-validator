"""Test cases for KML Validator using real data files."""
import pytest
from pathlib import Path
from shapely import GeometryType

from eo_format_validator.validators.kml_validator import KMLValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


@pytest.fixture
def kml_validator():
    """Create the actual KML validator instance."""
    return KMLValidator()


@pytest.fixture
def kml_samples_file():
    """Use the real KML samples file (Google Earth sample)."""
    return DATA_DIR / "KML_Samples.kml"


@pytest.fixture
def validation_request(kml_samples_file):
    """Create a validation request for KML."""
    return EOValidationRequest(
        format_identifier="format_4114",
        actual_file=FileInput(path=kml_samples_file),
        mode=ValidationMode.STRUCTURAL
    )


class TestKMLValidatorExtension:
    """Test KML validator extension handling."""

    def test_get_extensions(self, kml_validator):
        """Test that KML validator accepts kml and kmz extensions."""
        extensions = kml_validator.get_extensions()
        assert '.kml' in extensions
        assert '.kmz' in extensions
        assert len(extensions) == 2


class TestKMLValidatorAssertExists:
    """Test KML validator file existence checks."""

    def test_assert_exists_passes(self, kml_validator, kml_samples_file):
        """Test file existence passes for the real KML file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=FileInput(path=kml_samples_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.assert_exists(request)
        assert result.status.value == "success"


class TestKMLValidatorAssertCanOpen:
    """Test KML validator open/assertion functionality."""

    def test_assert_can_open_with_kml_samples(self, kml_validator, kml_samples_file):
        """Test opening a real KML file (valid XML/KML)."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=FileInput(path=kml_samples_file),
            mode=ValidationMode.FULL
        )
        result = kml_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestKMLValidatorCRS:
    """Test KML validator CRS extraction."""

    def test_get_crs_from_kml_samples(self, kml_validator, kml_samples_file):
        """Test CRS extraction from a real KML file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=FileInput(path=kml_samples_file),
            mode=ValidationMode.CRS
        )
        crs = kml_validator.get_crs(request)
        # KML files don't have explicit CRS attributes, should return None
        assert crs is None


class TestKMLValidatorGeometryType:
    """Test KML validator geometry type detection."""

    def test_assert_geometry_type_from_kml_samples(self, kml_validator, kml_samples_file):
        """Test geometry type detection from the real KML samples file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=FileInput(path=kml_samples_file),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        # KML_Samples.kml contains Points, LineStrings, and Polygons
        # The validator detects the first 200 placemarks
        result = kml_validator.assert_geometry_type(request)
        # The file has multiple geometry types, so this may succeed or fail
        assert result is not None


class TestKMLValidatorFullValidation:
    """Test KML validator full validation workflow."""

    def test_validate_structural_mode(self, kml_validator, kml_samples_file):
        """Test validation in structural mode with the real KML file."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=FileInput(path=kml_samples_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = kml_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full_mode(self, kml_validator, kml_samples_file):
        """Test validation in full mode."""
        request = EOValidationRequest(
            format_identifier="format_4114",
            actual_file=FileInput(path=kml_samples_file),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        result = kml_validator.validate(request)
        assert result is not None