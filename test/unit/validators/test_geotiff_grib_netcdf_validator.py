"""Test cases for GeoTIFF, GRIB, and NetCDF Validators using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.geotiff_validator import GeoTIFFValidator
from eo_format_validator.validators.grib_validator import GRIBValidator
from eo_format_validator.validators.netcdf_validator import NetCDFValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


# ============== GeoTIFF Validator Tests ==============

@pytest.fixture
def geotiff_validator():
    """Create the actual GeoTIFF validator instance."""
    return GeoTIFFValidator()


@pytest.fixture
def test_tif_file():
    """Use a real TIFF file from the data directory."""
    return DATA_DIR / "WSF2019_v1_8_48.tif"


class TestGeoTIFFValidatorExtension:
    """Test GeoTIFF validator extension handling."""

    def test_get_extensions(self, geotiff_validator):
        """Test that GeoTIFF validator accepts TIFF extensions."""
        extensions = geotiff_validator.get_extensions()
        assert '.tif' in extensions
        assert '.tiff' in extensions


class TestGeoTIFFValidatorAssertCanOpen:
    """Test GeoTIFF validator open/assertion functionality."""

    def test_assert_can_open(self, geotiff_validator, test_tif_file):
        """Test opening a real GeoTIFF file."""
        request = EOValidationRequest(
            format_identifier="format_4109",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.FULL
        )
        result = geotiff_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestGeoTIFFValidatorCRS:
    """Test GeoTIFF validator CRS functionality."""

    def test_get_crs(self, geotiff_validator, test_tif_file):
        """Test CRS extraction from a real GeoTIFF file."""
        request = EOValidationRequest(
            format_identifier="format_4109",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.CRS
        )
        crs = geotiff_validator.get_crs(request)
        assert crs is not None


class TestGeoTIFFValidatorFullValidation:
    """Test GeoTIFF validator full validation workflow."""

    def test_validate_structural(self, geotiff_validator, test_tif_file):
        """Test structural validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4109",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = geotiff_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full(self, geotiff_validator, test_tif_file):
        """Test full validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4109",
            actual_file=FileInput(path=test_tif_file),
            mode=ValidationMode.FULL
        )
        result = geotiff_validator.validate(request)
        assert result.status.value == "success"


# ============== GRIB Validator Tests ==============

@pytest.fixture
def grib_validator():
    """Create the actual GRIB validator instance."""
    return GRIBValidator()


@pytest.fixture
def test_grib_file():
    """Use a real GRIB file from the data directory."""
    return DATA_DIR / "grib_beispiel.grb"


class TestGRIBValidatorExtension:
    """Test GRIB validator extension handling."""

    def test_get_extensions(self, grib_validator):
        """Test that GRIB validator accepts GRIB extensions."""
        extensions = grib_validator.get_extensions()
        assert '.grib' in extensions
        assert '.grb' in extensions
        assert '.grib2' in extensions
        assert '.grb2' in extensions


class TestGRIBValidatorAssertCanOpen:
    """Test GRIB validator open/assertion functionality."""

    def test_assert_can_open(self, grib_validator, test_grib_file):
        """Test opening a real GRIB file with cfgrib/xarray."""
        request = EOValidationRequest(
            format_identifier="format_4113",
            actual_file=FileInput(path=test_grib_file),
            mode=ValidationMode.FULL
        )
        result = grib_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestGRIBValidatorCRS:
    """Test GRIB validator CRS functionality."""

    def test_get_crs(self, grib_validator, test_grib_file):
        """Test CRS extraction from a real GRIB file."""
        request = EOValidationRequest(
            format_identifier="format_4113",
            actual_file=FileInput(path=test_grib_file),
            mode=ValidationMode.CRS
        )
        crs = grib_validator.get_crs(request)
        # GRIB files should have a CRS derived from shapeOfTheEarth
        assert crs is not None


class TestGRIBValidatorFullValidation:
    """Test GRIB validator full validation workflow."""

    def test_validate_structural(self, grib_validator, test_grib_file):
        """Test structural validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4113",
            actual_file=FileInput(path=test_grib_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = grib_validator.validate(request)
        assert result.status.value == "success"


# ============== NetCDF Validator Tests ==============

@pytest.fixture
def netcdf_validator():
    """Create the actual NetCDF validator instance."""
    return NetCDFValidator()


@pytest.fixture
def test_netcdf_file():
    """Use a real NetCDF file from the data directory."""
    return DATA_DIR / "pr_2018.nc"


class TestNetCDFValidatorExtension:
    """Test NetCDF validator extension handling."""

    def test_get_extensions(self, netcdf_validator):
        """Test that NetCDF validator accepts NetCDF extensions."""
        extensions = netcdf_validator.get_extensions()
        assert '.cdf' in extensions
        assert '.nc4' in extensions
        assert '.nc' in extensions


class TestNetCDFValidatorAssertCanOpen:
    """Test NetCDF validator open/assertion functionality."""

    def test_assert_can_open(self, netcdf_validator, test_netcdf_file):
        """Test opening a real NetCDF file with xarray."""
        request = EOValidationRequest(
            format_identifier="format_4115",
            actual_file=FileInput(path=test_netcdf_file),
            mode=ValidationMode.FULL
        )
        result = netcdf_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestNetCDFValidatorCRS:
    """Test NetCDF validator CRS functionality."""

    def test_get_crs(self, netcdf_validator, test_netcdf_file):
        """Test CRS extraction from a real NetCDF file."""
        request = EOValidationRequest(
            format_identifier="format_4115",
            actual_file=FileInput(path=test_netcdf_file),
            mode=ValidationMode.CRS
        )
        crs = netcdf_validator.get_crs(request)
        # NetCDF files may or may not have CRS, just check the method doesn't crash
        assert crs is not None


class TestNetCDFValidatorFullValidation:
    """Test NetCDF validator full validation workflow."""

    def test_validate_structural(self, netcdf_validator, test_netcdf_file):
        """Test structural validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4115",
            actual_file=FileInput(path=test_netcdf_file),
            mode=ValidationMode.STRUCTURAL
        )
        result = netcdf_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full(self, netcdf_validator, test_netcdf_file):
        """Test full validation with real file."""
        request = EOValidationRequest(
            format_identifier="format_4115",
            actual_file=FileInput(path=test_netcdf_file),
            mode=ValidationMode.FULL
        )
        result = netcdf_validator.validate(request)
        assert result.status.value == "success"