import pytest
import sys
import types
from contextlib import contextmanager
from unittest.mock import patch

from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils.open_operations import open_with_fiona

# ----------FIXTURES----------
@pytest.fixture
def test_file(tmp_path):
    """Create test shp file."""
    file_path = tmp_path / "file.shp"
    file_path.write_bytes(b"CONTENT")
    return file_path


@pytest.fixture
def file_input(test_file):
    """Create FileInput for test file."""
    return FileInput(_path=test_file)


@pytest.fixture
def format_obj():
    """Create Format object."""
    return Format(_identifier="test_shp", _expected_crs_epsg=4326)


@pytest.fixture
def validation_result(format_obj):
    """Create ValidationResult."""
    return ValidationResult(_source=format_obj.get_identifier())

# --------FIONA TESTS---------

def test_open_with_fiona_success(tmp_path,
                                 format_obj,
                                 file_input,
                                 validation_result):
    """Fiona.open returns valid validation_result."""

    class FakeDataset:
        schema = {"geometry": "Point", "properties": {}}
        crs = {"init": "EPSG:4326"}

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    # fake fiona module and submodule
    fake_fiona = types.ModuleType("fiona")
    fake_fiona.open = fake_open
    fake_fiona_errors = types.ModuleType("fiona.errors")

    class FakeDriverError(Exception):
        pass

    fake_fiona_errors.DriverError = FakeDriverError

    # Inject fake modules
    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):

        result = open_with_fiona(format_obj, file_input, validation_result)

    assert result is validation_result
    assert len(validation_result.get_infos()) == 1
    assert result.get_infos()[0].get_code() == "OPEN_PASSED"
    assert validation_result.is_valid
    assert "opened" in result.get_infos()[0].get_message().lower()
    assert result.get_validated()

def test_open_with_fiona_schema_access_error(tmp_path,
                                 format_obj,
                                 file_input,
                                 validation_result):
    """If accessing schema/crs raises error, it should be caught as unexpected error."""

    class FakeDataset:
        @property
        def schema(self):
            raise ValueError("Cannot read schema")


        @property
        def crs(self):
            return {"init": "EPSG:4326"}

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    # fake fiona module and submodule
    fake_fiona = types.ModuleType("fiona")
    fake_fiona.open = fake_open
    fake_fiona_errors = types.ModuleType("fiona.errors")

    class FakeDriverError(Exception):
        pass
    fake_fiona_errors.DriverError = FakeDriverError

    # Inject fake modules
    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):
        result = open_with_fiona(format_obj, file_input, validation_result)

    assert result is validation_result
    assert len(validation_result.get_warnings()) == 1
    assert "open" in result.get_warnings()[0].get_message().lower()
    assert not result.get_validated()
    assert result.get_warnings()[0].get_code() == "OPEN_ERROR"
    assert validation_result.is_valid

def test_open_with_fiona_when_fiona_missing(tmp_path,
                                 format_obj,
                                 file_input,
                                 validation_result):
    """If fiona is not importable, a FIONA_MISSING warning should be added."""
    with patch('builtins.__import__', side_effect=ImportError("No module named 'rasterio'")):
        result = open_with_fiona(format_obj, file_input, validation_result)

    assert result.is_valid
    assert len(result.get_warnings()) == 1
    assert result.get_warnings()[0].get_code() == "FIONA_MISSING"
    assert "fiona" in result.get_warnings()[0].get_message()


def test_open_with_fiona_driver_error(tmp_path,
                                 format_obj,
                                 file_input,
                                 validation_result):
    """If fiona.open raises DriverError, OPEN_FAILED should be set as error."""

    class FakeDriverError(Exception):
        pass

    # fake fiona module and submodule
    fake_fiona = types.ModuleType("fiona")
    fake_fiona_errors = types.ModuleType("fiona.errors")
    fake_fiona_errors.DriverError = FakeDriverError

    def fake_open_raise(path):
        raise FakeDriverError("fake driver failure")
    fake_fiona.open = fake_open_raise

    # Inject fake modules
    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):
        result = open_with_fiona(format_obj, file_input, validation_result)

    assert len(validation_result.get_errors()) == 1
    assert result.get_errors()[0].get_code() == "OPEN_FAILED"
    assert not validation_result.is_valid
    assert result is validation_result
    assert "open" in result.get_errors()[0].get_message().lower()
    assert result.get_validated()