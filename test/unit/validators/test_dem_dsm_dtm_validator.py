"""Test cases for DEM, DSM, and DTM Validators using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.dem_validator import DEMValidator
from eo_format_validator.validators.dsm_validator import DSMValidator
from eo_format_validator.validators.dtm_validator import DTMValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


@pytest.fixture
def test_tif_file():
    """Use a real TIFF file from the data directory."""
    return DATA_DIR / "WSF2019_v1_8_48.tif"


# ============== DEM Validator Tests ==============

@pytest.fixture
def dem_validator():
    """Create the actual DEM validator instance."""
    return DEMValidator()


class TestDEMValidatorExtension:
    """Test DEM validator extension handling."""

    def test_get_extensions(self, dem_validator):
        """Test that DEM validator accepts TIFF extensions."""
        extensions = dem_validator.get_extensions()
        assert '.tif' in extensions
        assert '.tiff' in extensions


class TestDEMValidatorAssertCanOpen:
    """Test DEM validator open/assertion functionality."""

    def test_assert_can_open(self, dem_validator, test_tif_file):
        """Test opening a real raster file."""
        request = EOValidationRequest(
            format_identifier="format_4102",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.FULL
        )
        result = dem_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestDEMValidatorCRS:
    """Test DEM validator CRS functionality."""

    def test_get_crs(self, dem_validator, test_tif_file):
        """Test CRS extraction from a real raster file."""
        request = EOValidationRequest(
            format_identifier="format_4102",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.CRS
        )
        crs = dem_validator.get_crs(request)
        assert crs is not None


class TestDEMValidatorFullValidation:
    """Test DEM validator full validation workflow."""

    def test_validate_structural(self, dem_validator, test_tif_file):
        """Test structural validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4102",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = dem_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full(self, dem_validator, test_tif_file):
        """Test full validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4102",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.FULL
        )
        result = dem_validator.validate(request)
        assert result.status.value == "success"


# ============== DSM Validator Tests ==============

@pytest.fixture
def dsm_validator():
    """Create the actual DSM validator instance."""
    return DSMValidator()


class TestDSMValidatorExtension:
    """Test DSM validator extension handling."""

    def test_get_extensions(self, dsm_validator):
        """Test that DSM validator accepts TIFF extensions."""
        extensions = dsm_validator.get_extensions()
        assert '.tif' in extensions
        assert '.tiff' in extensions


class TestDSMValidatorAssertCanOpen:
    """Test DSM validator open/assertion functionality."""

    def test_assert_can_open(self, dsm_validator, test_tif_file):
        """Test opening a real raster file."""
        request = EOValidationRequest(
            format_identifier="format_4103",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.FULL
        )
        result = dsm_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestDSMValidatorCRS:
    """Test DSM validator CRS functionality."""

    def test_get_crs(self, dsm_validator, test_tif_file):
        """Test CRS extraction from a real raster file."""
        request = EOValidationRequest(
            format_identifier="format_4103",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.CRS
        )
        crs = dsm_validator.get_crs(request)
        assert crs is not None


class TestDSMValidatorFullValidation:
    """Test DSM validator full validation workflow."""

    def test_validate_structural(self, dsm_validator, test_tif_file):
        """Test structural validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4103",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = dsm_validator.validate(request)
        assert result.status.value == "success"


# ============== DTM Validator Tests ==============

@pytest.fixture
def dtm_validator():
    """Create the actual DTM validator instance."""
    return DTMValidator()


class TestDTMValidatorExtension:
    """Test DTM validator extension handling."""

    def test_get_extensions(self, dtm_validator):
        """Test that DTM validator accepts TIFF extensions."""
        extensions = dtm_validator.get_extensions()
        assert '.tif' in extensions
        assert '.tiff' in extensions


class TestDTMValidatorAssertCanOpen:
    """Test DTM validator open/assertion functionality."""

    def test_assert_can_open(self, dtm_validator, test_tif_file):
        """Test opening a real raster file."""
        request = EOValidationRequest(
            format_identifier="format_4104",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.FULL
        )
        result = dtm_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestDTMValidatorCRS:
    """Test DTM validator CRS functionality."""

    def test_get_crs(self, dtm_validator, test_tif_file):
        """Test CRS extraction from a real raster file."""
        request = EOValidationRequest(
            format_identifier="format_4104",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.CRS
        )
        crs = dtm_validator.get_crs(request)
        assert crs is not None


class TestDTMValidatorFullValidation:
    """Test DTM validator full validation workflow."""

    def test_validate_structural(self, dtm_validator, test_tif_file):
        """Test structural validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4104",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = dtm_validator.validate(request)
        assert result.status.value == "success"