import types
import sys
from contextlib import contextmanager
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List
from eo_format_validator import FileInput, Format, ValidationResult, RasterFileValidator


# ------TEST VALIDATOR---------

class MockRasterFileValidator(RasterFileValidator):

    def _get_extensions(self) -> List[str]:
        return ['.tif', '.tiff']



# ----------FIXTURES----------

@pytest.fixture
def raster_validator():
    """Create test raster file validator instance."""
    return MockRasterFileValidator()


@pytest.fixture
def test_file(tmp_path):
    """Create test raster file."""
    file_path = tmp_path / "test.tif"
    file_path.write_bytes(b"CONTENT")
    return file_path


@pytest.fixture
def file_input(test_file):
    """Create FileInput for test file."""
    return FileInput(_path=test_file)


@pytest.fixture
def format_obj():
    """Create Format object."""
    return Format(_identifier="test_raster", _expected_crs_epsg=4326)


@pytest.fixture
def validation_result(format_obj):
    """Create ValidationResult."""
    return ValidationResult(_source=format_obj.get_identifier())



# -----_validate_open() TESTS-------

def test_validate_open_succeeds_with_valid_file(tmp_path,
                                                raster_validator,
                                                format_obj,
                                                file_input,
                                                validation_result):
    """Test successful file opening with valid raster."""
    class FakeDataset:
        width = 1024
        height = 768

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    # fake rasterio module and rasterio.errors submodule
    fake_rasterio = types.ModuleType("rasterio")
    fake_rasterio.open = fake_open
    fake_rasterio_errors = types.ModuleType("rasterio.errors")

    class FakeRasterioIOError(Exception):
        pass
    fake_rasterio_errors.RasterioIOError = FakeRasterioIOError

    # Inject fake modules
    with patch.dict(sys.modules, {"rasterio": fake_rasterio, "rasterio.errors": fake_rasterio_errors}):

        result = raster_validator._validate_open(format_obj, file_input, validation_result)

    assert result is validation_result
    assert result.is_valid
    assert result.get_validated()
    assert len(result.get_infos()) == 1
    assert result.get_infos()[0].get_code() == "OPEN_PASSED"
    assert "opened" in result.get_infos()[0].get_message().lower()

def test_validate_open_fails_with_invalid_dimensions(tmp_path,
                                                     raster_validator,
                                                     format_obj,
                                                     file_input,
                                                     validation_result):
    """Test that invalid dimensions (width/height <= 0) are caught."""
    class FakeDataset:
        width = 0
        height = -1

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    # fake rasterio module and rasterio.errors submodule
    fake_rasterio = types.ModuleType("rasterio")
    fake_rasterio.open = fake_open
    fake_rasterio_errors = types.ModuleType("rasterio.errors")

    class FakeRasterioIOError(Exception):
        pass
    fake_rasterio_errors.RasterioIOError = FakeRasterioIOError

    # Inject fake modules
    with patch.dict(sys.modules, {"rasterio": fake_rasterio, "rasterio.errors": fake_rasterio_errors}):
        result = raster_validator._validate_open(format_obj, file_input, validation_result)

    assert not result.is_valid
    assert len(result.get_errors()) == 1
    assert result.get_errors()[0].get_code() == "INVALID_DIMENSIONS"
    assert "invalid raster dimensions" in result.get_errors()[0].get_message().lower()

def test_validate_open_handles_missing_rasterio(raster_validator, format_obj,
                                                file_input, validation_result):
    """Test handling when rasterio is not installed."""
    with patch('builtins.__import__', side_effect=ImportError("No module named 'rasterio'")):
        result = raster_validator._validate_open(format_obj, file_input, validation_result)

    assert result.is_valid
    assert len(result.get_warnings()) == 1
    assert result.get_warnings()[0].get_code() == "RASTERIO_MISSING"
    assert "RasterIO" in result.get_warnings()[0].get_message()

def test_validate_open_handles_rasterio_io_error(tmp_path,
                                                 raster_validator,
                                                 format_obj,
                                                 file_input,
                                                 validation_result):
    """Test handling of RasterioIOError."""

    # fake rasterio module and rasterio.errors submodule
    fake_rasterio = types.ModuleType("rasterio")
    fake_rasterio_errors = types.ModuleType("rasterio.errors")

    class FakeRasterioIOError(Exception):
        pass

    fake_rasterio_errors.RasterioIOError = FakeRasterioIOError

    def fake_open(path):
        raise FakeRasterioIOError("Cannot open file")

    fake_rasterio.open = fake_open

    # Inject fake modules
    with patch.dict(sys.modules, {"rasterio": fake_rasterio, "rasterio.errors": fake_rasterio_errors}):
        result = raster_validator._validate_open(format_obj, file_input, validation_result)

    # verify: error due to _validate_open logic
    assert not result.is_valid
    assert len(result.get_errors()) == 1
    assert result.get_errors()[0].get_code() == "OPEN_FAILED"


# -------_validate_crs() TESTS--------
def test_validate_crs_succeeds_with_valid_crs(tmp_path,
                                              raster_validator,
                                              format_obj,
                                              file_input,
                                              validation_result):
    """Test successful CRS validation."""
    # fake rasterio module and rasterio.errors submodule
    fake_rasterio = types.ModuleType("rasterio")
    fake_rasterio_errors = types.ModuleType("rasterio.errors")

    class FakeDataset:
        def __init__(self):
            self.crs = {"init": "EPSG:4326"}

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    fake_rasterio.open = fake_open

    class FakeRasterioIOError(Exception):
        pass

    fake_rasterio_errors.RasterioIOError = FakeRasterioIOError

    # Inject fake modules
    with patch.dict(sys.modules, {"rasterio": fake_rasterio, "rasterio.errors": fake_rasterio_errors}), patch("eo_format_validator.validators.raster_file_validator.compare_crs") as mock_compare_crs:
        success_result = ValidationResult()
        success_result.set_success("CRS valid", "CRS_MATCH")
        mock_compare_crs.return_value = success_result

        result = raster_validator._validate_crs(format_obj, file_input, validation_result)

    assert result.is_valid
    assert len(result.get_errors()) == 0
    assert len(result.get_warnings()) == 0
    assert len(result.get_infos()) == 1
    assert result.get_infos()[0].get_code() == "CRS_MATCH"
    mock_compare_crs.assert_called_once()

def test_validate_crs_warns_when_crs_missing(raster_validator,
                                             format_obj, file_input, validation_result):
    """Test that missing CRS is handled gracefully."""
    # fake rasterio module and rasterio.errors submodule
    fake_rasterio = types.ModuleType("rasterio")
    fake_rasterio_errors = types.ModuleType("rasterio.errors")

    class FakeDataset:
        def __init__(self):
            self.crs = None

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    fake_rasterio.open = fake_open

    class FakeRasterioIOError(Exception):
        pass

    fake_rasterio_errors.RasterioIOError = FakeRasterioIOError

    # Inject fake modules
    with patch.dict(sys.modules, {"rasterio": fake_rasterio, "rasterio.errors": fake_rasterio_errors}), patch(
        "eo_format_validator.validators.raster_file_validator.compare_crs"
    ) as mock_compare_crs:
        success_result = ValidationResult()
        success_result.add_warning("CRS missing", "CRS_MISSING")
        mock_compare_crs.return_value = success_result

        result = raster_validator._validate_crs(format_obj, file_input, validation_result)

    assert result.is_valid
    assert len(result.get_errors()) == 0
    assert len(result.get_warnings()) == 1
    assert len(result.get_infos()) == 0
    assert result.get_warnings()[0].get_code() == "CRS_MISSING"
    assert "no crs" in result.get_warnings()[0].get_message().lower()


def test_validate_crs_handles_missing_rasterio(raster_validator, format_obj,
                                               file_input, validation_result):
    """Test handling when rasterio is not installed."""

    with patch('builtins.__import__', side_effect=ImportError("No module named 'rasterio'")):
        result = raster_validator._validate_crs(format_obj, file_input, validation_result)

    # Should add warning
    assert result.is_valid
    assert len(result.get_warnings()) == 1
    assert result.get_warnings()[0].get_code() == "RASTERIO_MISSING"


def test_validate_crs_handles_rasterio_io_error(raster_validator,
                                             format_obj, file_input, validation_result):
    """Test handling of RasterioIOError during CRS read."""
    # fake rasterio module and rasterio.errors submodule
    fake_rasterio = types.ModuleType("rasterio")
    fake_rasterio_errors = types.ModuleType("rasterio.errors")

    def fake_open(path):
        raise FakeRasterioIOError("Cannot read CRS")

    fake_rasterio.open = fake_open

    class FakeRasterioIOError(Exception):
        pass

    fake_rasterio_errors.RasterioIOError = FakeRasterioIOError

    # Inject fake modules
    with patch.dict(sys.modules, {"rasterio": fake_rasterio, "rasterio.errors": fake_rasterio_errors}):

        result = raster_validator._validate_crs(format_obj, file_input, validation_result)

    assert result.is_valid
    assert len(result.get_warnings()) == 1
    assert result.get_warnings()[0].get_code() == "CRS_FAILED"
