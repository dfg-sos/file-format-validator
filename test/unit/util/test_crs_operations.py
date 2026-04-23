import sys
import types
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from eo_format_validator.core.file_input import FileInput
from eo_format_validator.core.format import Format
from eo_format_validator.result.validation_result import ValidationResult
from eo_format_validator.utils import crs_operations


# helper for ValidationResult contents
#def _has_code(validation_result: ValidationResult, code: str) -> bool:
#    """Find a code in any of validation_result's collections (errors/warnings/infos)."""
#    for attr in ("errors", "warnings", "infos"):
#        coll = getattr(validation_result, attr, None)
#        if coll:
#            for item in coll:
#                msg_code = None
#                if hasattr(item, "code"):
#                    msg_code = getattr(item, "code")
#                elif isinstance(item, dict):
#                    msg_code = item.get("code")
#                elif isinstance(item, str):
#                    if code.lower() in item.lower():
#                        return True
#                if msg_code == code:
#                    return True
#    return False

def _has_code(validation_result: ValidationResult, code: str) -> bool:
    """Find a code in any of validation_result's collections (errors/warnings/infos)."""

    collections = [
        validation_result.get_errors(),
        validation_result.get_warnings(),
        validation_result.get_infos(),
    ]

    for coll in collections:
        if not coll:
            continue

        for item in coll:

            if hasattr(item, "get_code"):
                msg_code = item.get_code()

                if msg_code == code:
                    return True

    return False

# --------normalize_crs_to_epsg tests----------
@pytest.mark.parametrize(
    "inp, expected",
    [
        (4326, 4326),
        (3927, 3927),
        (4826, 4826),
        ("EPSG:4326", 4326),
        ("EPSG:5273", 5273),
        ("EPSG:2792", 2792),
        ("4326", 4326),
        (" epsg4326 ", 4326),
        ("EPSG4326", 4326),
        ("epsg:4326", 4326),
        ("EPSG:abcd", None),
        ("not a crs", None),
        (None, None),
    ],
)
def test_normalize_crs_to_epsg_strings_and_ints(inp, expected):
    assert crs_operations.normalize_crs_to_epsg(inp) == expected


def test_normalize_crs_to_epsg_object_with_to_epsg():
    class FakeCRSClass:
        def to_epsg(self):
            return 1234

    assert crs_operations.normalize_crs_to_epsg(FakeCRSClass()) == 1234


def test_normalize_crs_to_epsg_dict_init_case():
    d = {"init": "EPSG:4326"}
    assert crs_operations.normalize_crs_to_epsg(d) == 4326

    d_bad = {"init": "EPSG:abc"}
    assert crs_operations.normalize_crs_to_epsg(d_bad) is None


# -----------compare_crs tests------------

def test_compare_crs_expected_present_actual_missing_adds_warning(tmp_path):
    file_format = Format("test_format", 4326)
    validation_result = ValidationResult(_source="test")

    class NoEPSG:
        pass

    test_path = tmp_path / "test.tif"
    test_path.write_bytes(b"CONTENT")

    res = crs_operations.compare_crs(NoEPSG(), file_format, test_path, validation_result)
    assert res is validation_result
    assert _has_code(validation_result, "EPSG_MISSING")


def test_compare_crs_expected_none_actual_found_adds_info(tmp_path):
    file_format = Format("test_format", None)
    validation_result = ValidationResult(_source="test")

    test_path = tmp_path / "test.tif"
    test_path.write_bytes(b"CONTENT")

    res = crs_operations.compare_crs("EPSG:4326", file_format, test_path, validation_result)
    assert res is validation_result
    assert _has_code(validation_result, "EPSG_FOUND")


def test_compare_crs_both_none_adds_no_crs_info(tmp_path):
    file_format = Format("test_format", None)
    validation_result = ValidationResult(_source="test")

    test_path = tmp_path / "test.tif"
    test_path.write_bytes(b"CONTENT")

    res = crs_operations.compare_crs(None, file_format, test_path, validation_result)
    assert res is validation_result
    assert _has_code(validation_result, "NO_CRS")


def test_compare_crs_mismatch_sets_failure(tmp_path):
    file_format = Format("test_format", 4326)
    validation_result = ValidationResult(_source="test")

    test_path = tmp_path / "test.tif"
    test_path.write_bytes(b"CONTENT")

    res = crs_operations.compare_crs("EPSG:3857", file_format, test_path, validation_result)
    assert res is validation_result
    assert _has_code(validation_result, "CRS_MISMATCH")


def test_compare_crs_match_sets_success(tmp_path):
    file_format = Format("test_format", 4326)
    validation_result = ValidationResult(_source="test")

    test_path = tmp_path / "test.tif"
    test_path.write_bytes(b"CONTENT")

    res = crs_operations.compare_crs("EPSG:4326", file_format, test_path, validation_result)
    assert res is validation_result
    assert _has_code(validation_result, "CRS_MATCH")



# ---------validate_crs_with_fiona tests--------

def test_validate_crs_with_fiona_when_fiona_missing(tmp_path):
    """If fiona is not importable, a FIONA_MISSING warning should be added."""
    import builtins
    # make __import__ raise ImportError for fiona
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "fiona" or name.startswith("fiona."):
            raise ImportError("no fiona")
        return real_import(name, globals, locals, fromlist, level)

    file_format = Format("test_shp", 4326)
    test_path = tmp_path / "file.shp"
    test_path.write_bytes(b"CONTENTS")

    file_input = FileInput(test_path)
    validation_result = ValidationResult(_source="test")

    with patch("builtins.__import__", side_effect=fake_import):
        res = crs_operations.validate_crs_with_fiona(file_format, file_input, validation_result)

    assert res is validation_result
    assert _has_code(validation_result, "FIONA_MISSING")

def test_validate_crs_with_fiona_driver_error(tmp_path):
    fake_fiona = types.ModuleType("fiona")

    class FakeDriverError(Exception):
        pass

    fake_fiona_errors = types.ModuleType("fiona.errors")
    fake_fiona_errors.DriverError = FakeDriverError

    def fake_open_raise(path):
        raise FakeDriverError("fake driver failure")

    fake_fiona.open = fake_open_raise

    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):
        file_format = Format("test_shp", 4326)
        test_path = tmp_path / "file.shp"
        test_path.write_bytes(b"CONTENTS")

        file_input = FileInput(test_path)
        validation_result = ValidationResult(_source="test")

        res = crs_operations.validate_crs_with_fiona(file_format, file_input, validation_result)

    assert res is validation_result
    assert _has_code(validation_result, "CRS_FAILED")

def test_validate_crs_with_fiona_success(tmp_path):
    """fiona.open returns an object with crs, compare_crs path executed successfully."""

    class FakeOpen:
        def __init__(self):
            self.crs = {"init": "EPSG:4326"}

    @contextmanager
    def fake_open(path):
        yield FakeOpen()

    # Build fake fiona module and fiona.errors submodule
    fake_fiona = types.ModuleType("fiona")
    fake_fiona.open = fake_open
    fake_fiona_errors = types.ModuleType("fiona.errors")

    class FakeDriverError(Exception):
        pass
    fake_fiona_errors.DriverError = FakeDriverError

    # Inject modules into sys.modules for the duration of the test
    with patch.dict(sys.modules, {"fiona": fake_fiona, "fiona.errors": fake_fiona_errors}):
        test_path = tmp_path / "file.shp"
        test_path.write_bytes(b"CONTENTS")

        file_input = FileInput(test_path)
        validation_result = ValidationResult(_source="test")
        file_format = Format("test_format", 4326)

        res = crs_operations.validate_crs_with_fiona(file_format, file_input, validation_result)

    assert res is validation_result

    assert _has_code(validation_result, "CRS_MATCH")