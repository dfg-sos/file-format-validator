"""Test cases for Shapefile Validator using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.shapefile_validator import ShapefileValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, MultiFileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")
SHAPEFILE_DIR = DATA_DIR / "Shapefile1"


@pytest.fixture
def shapefile_validator():
    """Create the actual Shapefile validator instance."""
    return ShapefileValidator()


@pytest.fixture
def shapefile_files():
    """Use the real shapefile and its auxiliary files."""
    shp_file = DATA_DIR / "gis_osm_buildings_a_free_1.shp"
    shx_file = DATA_DIR / "gis_osm_buildings_a_free_1.shx"
    dbf_file = DATA_DIR / "gis_osm_buildings_a_free_1.dbf"
    prj_file = DATA_DIR / "gis_osm_buildings_a_free_1.prj"
    cpg_file = DATA_DIR / "gis_osm_buildings_a_free_1.cpg"
    return shp_file, shx_file, dbf_file, prj_file, cpg_file


class TestShapefileValidatorExtension:
    """Test Shapefile validator extension handling."""

    def test_get_extensions(self, shapefile_validator):
        """Test that Shapefile validator accepts .shp extension."""
        extensions = shapefile_validator.get_extensions()
        assert '.shp' in extensions
        assert len(extensions) == 1


class TestShapefileValidatorAssertExtension:
    """Test Shapefile validator extension and multi-file assertion."""

    def test_assert_extension_with_all_required_files(self, shapefile_validator, shapefile_files):
        """Test extension validation with all required files present."""
        shp_file, shx_file, dbf_file, prj_file, cpg_file = shapefile_files
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files={shx_file, dbf_file, prj_file, cpg_file}
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.assert_extension(request)
        assert result.status.value == "success"

    def test_assert_extension_missing_required(self, shapefile_validator):
        """Test extension validation fails when required files are missing."""
        shp_file = Path("/fake/file.shp")
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files=set()
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.assert_extension(request)
        assert result.status.value == "failure"

    def test_assert_extension_with_optional_files(self, shapefile_validator, shapefile_files):
        """Test extension validation with optional files present."""
        shp_file, shx_file, dbf_file, prj_file, cpg_file = shapefile_files
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files={shx_file, dbf_file, prj_file, cpg_file}
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.assert_extension(request)
        assert result.status.value == "success"


class TestShapefileValidatorFullValidation:
    """Test Shapefile validator full validation workflow."""

    def test_validate_structural_mode(self, shapefile_validator, shapefile_files):
        """Test validation in structural mode with real shapefile files."""
        shp_file, shx_file, dbf_file, prj_file, cpg_file = shapefile_files
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files={shx_file, dbf_file, prj_file, cpg_file}
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full_mode(self, shapefile_validator, shapefile_files):
        """Test validation in full mode (opens via fiona)."""
        shp_file, shx_file, dbf_file, prj_file, cpg_file = shapefile_files
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files={shx_file, dbf_file, prj_file, cpg_file}
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.FULL
        )
        result = shapefile_validator.validate(request)
        assert result.status.value == "success"