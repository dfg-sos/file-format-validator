import pytest
import sys
import types

from contextlib import contextmanager
from unittest.mock import patch

from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format,ShapeType
from eo_format_validator.model.validation_result import ValidationResult
from eo_format_validator.utils import shape_operations

# ----------FIXTURES----------
@pytest.fixture
def test_file(tmp_path):
    """Create test shp file."""
    file_path = tmp_path / "file.gpkg"
    file_path.write_bytes(b"CONTENT")
    return file_path


@pytest.fixture
def file_input(test_file):
    """Create FileInput for test file."""
    return FileInput(_path=test_file)


@pytest.fixture
def format_obj():
    """Create Format object."""
    return Format(_identifier="test_shp", _expected_crs_epsg=4326, _shape_type=ShapeType.MULTIPOINT)


@pytest.fixture
def validation_result(format_obj):
    """Create ValidationResult."""
    return ValidationResult(_source=format_obj.get_identifier())

# -----------normalize_geometry_to_shape_type() tests----------

@pytest.mark.parametrize("input_name,expected_shape_type", [

    ("point", ShapeType.POINT),
    ("Point", ShapeType.POINT),
    ("POINT", ShapeType.POINT),
    ("PoInT", ShapeType.POINT),

    ("multipoint", ShapeType.MULTIPOINT),
    ("multi point", ShapeType.MULTIPOINT),
    ("MULTI point", ShapeType.MULTIPOINT),
    ("multiPOINT", ShapeType.MULTIPOINT),

    ("linestring", ShapeType.LINESTRING),
    ("line string", ShapeType.LINESTRING),
    ("line", ShapeType.LINESTRING),
    ("LINEstring", ShapeType.LINESTRING),

    ("multilinestring", ShapeType.MULTILINESTRING),
    ("multi line", ShapeType.MULTILINESTRING),

    ("polygon", ShapeType.POLYGON),
    ("Polygon", ShapeType.POLYGON),
    ("multipolygon", ShapeType.MULTIPOLYGON),
    ("multi polygon", ShapeType.MULTIPOLYGON),

    ("triangle", ShapeType.TRIANGLE),
    ("tin", ShapeType.TIN),
    ("geometrycollection", ShapeType.GEOMETRYCOLLECTION),

    ("unknown", ShapeType.OTHER),
    ("", ShapeType.OTHER),
    ("  ", ShapeType.OTHER),
    ("otherTYPE", ShapeType.OTHER),
    ("error", ShapeType.OTHER),
])
def test_normalize_geometry_to_shape_type(input_name, expected_shape_type):
    """Test geometry string representation to WKT ShapeType normalization."""
    result = shape_operations.normalize_geometry_to_shape_type(input_name)
    assert result == expected_shape_type


def test_normalize_geometry_to_shape_type_with_none():
    """Test that None input returns OTHER.
       OTHER is the default implementation also if ShapeType does not exist in a file."""
    result = shape_operations.normalize_geometry_to_shape_type(None)
    assert result == ShapeType.OTHER


# -----validate_shape_type_with_fiona() tests-----

def test_validate_shape_type_with_fiona_missing_library(tmp_path,
                                 format_obj,
                                 file_input,
                                 validation_result):
    """Test FIONA_MISSING when library not available."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "fiona" or name.startswith("fiona."):
            raise ImportError("no fiona")
        return real_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=fake_import):
        result = shape_operations.validate_shape_type_with_fiona(
            format_obj, file_input, validation_result
        )

    assert result is validation_result
    assert result.is_valid
    assert len(result.get_warnings()) == 1
    assert result.get_warnings()[0].get_code() == "FIONA_MISSING"
    assert "fiona" in result.get_warnings()[0].get_message()

def test_validate_shape_type_with_fiona_shape_match(tmp_path,
                                 format_obj,
                                 file_input,
                                 validation_result):
    """Test SHAPE_MATCH when geometry matches expected."""

    class FakeDataset:
        schema = {"geometry": "multipoint", "properties": {}}

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    fake_fiona = types.ModuleType("fiona")
    fake_fiona.open = fake_open
    fake_fiona_errors = types.ModuleType("fiona.errors")

    class FakeDriverError(Exception):
        pass

    fake_fiona_errors.DriverError = FakeDriverError

    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):

        result = shape_operations.validate_shape_type_with_fiona(
            format_obj, file_input, validation_result
        )

    assert validation_result.is_valid
    assert result is validation_result
    assert len(validation_result.get_infos()) == 1
    assert result.get_infos()[0].get_code() == "SHAPE_MATCH"
    assert "shape" in result.get_infos()[0].get_message().lower()
    assert result.get_validated()


def test_validate_shape_type_with_fiona_shape_mismatch(tmp_path,
                                 format_obj,
                                 file_input,
                                 validation_result):
    """Test SHAPE_MISMATCH when geometry doesn't match expected."""

    class FakeDataset:
        schema = {"geometry": "Point", "properties": {}}

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    fake_fiona = types.ModuleType("fiona")
    fake_fiona.open = fake_open
    fake_fiona_errors = types.ModuleType("fiona.errors")

    class FakeDriverError(Exception):
        pass
    fake_fiona_errors.DriverError = FakeDriverError

    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):
        result = shape_operations.validate_shape_type_with_fiona(
            format_obj, file_input, validation_result
        )
    assert not validation_result.is_valid
    assert result is validation_result
    assert len(validation_result.get_errors()) == 1
    assert result.get_errors()[0].get_code() == "SHAPE_MISMATCH"
    #assert any(error.get_code() == "GEOMETRY_DETECTED" for error in result.get_errors())
    assert "shape" in result.get_errors()[0].get_message().lower()
    assert result.get_validated()


def test_validate_shape_type_with_fiona_no_expected_shape(tmp_path,

                                 file_input,
                                 validation_result):
    """Test SHAPE_FOUND when no expected shape given."""

    class FakeDataset:
        schema = {"geometry": "Polygon", "properties": {}}

    @contextmanager
    def fake_open(path):
        yield FakeDataset()

    fake_fiona = types.ModuleType("fiona")
    fake_fiona.open = fake_open
    fake_fiona_errors = types.ModuleType("fiona.errors")

    class FakeDriverError(Exception):
        pass

    fake_fiona_errors.DriverError = FakeDriverError

    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):
        file_format = Format("test_gpkg")  # no shape_type
        result = shape_operations.validate_shape_type_with_fiona(
            file_format, file_input, validation_result
        )

    assert validation_result.is_valid
    assert result is validation_result
    assert any(info.get_code() == "SHAPE_FOUND" for info in result.get_infos())
    assert len(validation_result.get_errors()) == 0
    assert len(validation_result.get_warnings()) == 0
    if result.get_infos():
        assert "shape" in result.get_infos()[0].get_message().lower()
    assert not result.get_validated()

# -------compare_shape_type() tests---------

@pytest.mark.parametrize("expected,actual,expected_code,expected_valid", [
    # both present and match
    (ShapeType.POLYGON, ShapeType.POLYGON, "SHAPE_MATCH", True),
    (ShapeType.POINT, ShapeType.POINT, "SHAPE_MATCH", True),

    # both present but mismatch
    (ShapeType.POLYGON, ShapeType.POINT, "SHAPE_MISMATCH", False),
    (ShapeType.LINESTRING, ShapeType.POLYGON, "SHAPE_MISMATCH", False),

    # expected but no actual
    (ShapeType.POLYGON, None, "SHAPE_MISSING", True),  # warning, no error

    # no expected but actual found
    (None, ShapeType.POLYGON, "SHAPE_FOUND", True),
    (None, ShapeType.POINT, "SHAPE_FOUND", True),

    # neither expected nor actual
    (None, None, "NO_SHAPES", True),  # warning
])
def test_compare_shape_type(expected, actual, expected_code, expected_valid):
    """Test shape type comparison logic."""
    validation_result = ValidationResult(_source="test")

    result = shape_operations.compare_shape_type(expected, actual, validation_result)

    assert result is validation_result
    if result.get_infos():
        assert result.get_infos()[0].get_code() == expected_code
    elif result.get_warnings():
        assert result.get_warnings()[0].get_code() == expected_code
    else:
        assert result.get_errors()[0].get_code() == expected_code
    assert validation_result.is_valid == expected_valid
