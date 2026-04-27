import pytest
from typing import List

from eo_format_validator.model.file_format_validator import FileFormatValidator
from eo_format_validator.model.validation_mode import ValidationMode
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.model.validation_result import ValidationResult


# -------TEST VALIDATOR--------

class MockFileFormatValidator(FileFormatValidator):

    def _get_extensions(self) -> List[str]:
        return ['.test', '.tst']

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        validation_result.set_success("File opened successfully", "OPEN_PASSED")
        return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        validation_result.set_success("CRS validated", "CRS_MATCH")
        return validation_result


class FailingMockFileFormatValidator(FileFormatValidator):

    def _get_extensions(self) -> List[str]:
        return ['.test']

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        validation_result.set_failure("Failed to open file", "OPEN_FAILED")
        return validation_result

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        validation_result.set_failure("CRS mismatch", "CRS_MISMATCH")
        return validation_result



# ------FIXTURES-------------

@pytest.fixture
def test_validator():
    return MockFileFormatValidator()


@pytest.fixture
def failing_validator():
    return FailingMockFileFormatValidator()


@pytest.fixture
def test_file_matching_extension(tmp_path):
    file_path = tmp_path / "test.test"
    file_path.write_bytes(b"CONTENT")
    return file_path


@pytest.fixture
def test_file_wrong_extension(tmp_path):
    file_path = tmp_path / "test.wrong"
    file_path.write_bytes(b"CONTENT")
    return file_path


@pytest.fixture
def format_obj():
    return Format(_identifier="test_format")


# ------MODE TESTS-----------

def test_structural_mode_validates_extension_only(test_validator, format_obj,
                                                  test_file_matching_extension):
    """Test that structural mode only validates extension."""
    file_input = FileInput(_path=test_file_matching_extension)

    result = test_validator.validate(format_obj, file_input, ValidationMode.STRUCTURAL)

    assert result.is_valid
    assert len(result.get_infos()) == 1
    assert "extension" in result.get_infos()[0].get_message().lower()
    assert result.get_infos()[0].get_code() == "EXT_PASSED"


def test_crs_mode_validates_crs_only(test_validator, format_obj,
                                     test_file_matching_extension):
    """Test that CRS mode only validates CRS."""
    file_input = FileInput(_path=test_file_matching_extension)

    result = test_validator.validate(format_obj, file_input, ValidationMode.CRS)

    assert result.is_valid
    assert len(result.get_infos()) == 1
    assert result.get_infos()[0].get_code() == "CRS_MATCH"


def test_strict_mode_validates_all(test_validator, format_obj,
                                   test_file_matching_extension):
    """Test that STRICT mode validates extension, open, and CRS."""
    file_input = FileInput(_path=test_file_matching_extension)

    result = test_validator.validate(format_obj, file_input, ValidationMode.STRICT)

    assert result.is_valid
    assert len(result.get_infos()) == 3

    codes = [info.get_code() for info in result.get_infos()]
    assert "EXT_PASSED" in codes
    assert "OPEN_PASSED" in codes
    assert "CRS_MATCH" in codes


# ------EXTENSION VALIDATION TESTS-----

def test_extension_validation_passes_with_matching_extension(test_validator, format_obj,
                                                             test_file_matching_extension):
    """Test that extension validation passes with correct extension."""
    file_input = FileInput(_path=test_file_matching_extension)
    validation_result = ValidationResult(_source=format_obj.get_identifier())

    result = test_validator._validate_extension(format_obj, file_input, validation_result)

    assert result.is_valid
    assert len(result.get_infos()) == 1
    assert result.get_infos()[0].get_code() == "EXT_PASSED"


def test_extension_validation_fails_with_wrong_extension(test_validator, format_obj,
                                                         test_file_wrong_extension):
    """Test that extension validation fails with wrong extension."""
    file_input = FileInput(_path=test_file_wrong_extension)
    validation_result = ValidationResult(_source=format_obj.get_identifier())

    result = test_validator._validate_extension(format_obj, file_input, validation_result)

    assert not result.is_valid
    assert len(result.get_errors()) == 1
    assert result.get_errors()[0].get_code() == "EXT_MISMATCH"
    assert "extension" in result.get_errors()[0].get_message().lower()


# ---------STRICT MODE TEST----------

def test_strict_mode_fails_if_any_validation_fails(failing_validator, format_obj,
                                                   test_file_matching_extension):
    """Test that STRICT mode fails if any sub-validation fails."""
    file_input = FileInput(_path=test_file_matching_extension)

    result = failing_validator.validate(format_obj, file_input, ValidationMode.STRICT)

    # Should be invalid because open and CRS failed
    assert not result.is_valid
    assert len(result.get_errors()) == 2

    # Extension should have passed
    assert len(result.get_infos()) == 1
    assert result.get_infos()[0].get_code() == "EXT_PASSED"


# -------PARAMETRIZED TEST-----

@pytest.mark.parametrize("extension", ['.test', '.tst', '.TEST', '.TST'])
def test_extension_case_insensitive(test_validator, format_obj, tmp_path, extension):
    """Test that extension validation is case-insensitive."""
    file_path = tmp_path / f"test{extension}"
    file_path.write_bytes(b"CONTENT")

    file_input = FileInput(_path=file_path)

    result = test_validator.validate(format_obj, file_input, ValidationMode.STRUCTURAL)

    assert result.is_valid