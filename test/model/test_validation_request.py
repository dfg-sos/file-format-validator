import pytest
from pathlib import Path
from format_validator import ValidationRequest, ValidationMode, FileInput,FormatIdentifier

@pytest.fixture
def validation_request():
    return ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.STRUCTURAL
    )

def test_enabled_modes(validation_request):
    assert validation_request.enabled_modes() == [ValidationMode.BASIC, ValidationMode.STRUCTURAL, ValidationMode.FULL]

def test_post_init_valid_mode():
    try:
        ValidationRequest(
            format_identifier=FormatIdentifier.GIS,
            actual_file=FileInput(path=Path("test.txt")),
            mode=ValidationMode.CRS
        )
        assert False, "Expected an AssertionError for unsupported validation mode."
    except AssertionError:
        pass

def test_equality(validation_request):
    same_request = ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.STRUCTURAL
    )
    different_input = ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("different.txt")),
        mode=ValidationMode.STRUCTURAL
    )
    different_format = ValidationRequest(
        format_identifier=FormatIdentifier.GEOTIFF,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.STRUCTURAL
    )

    different_mode = ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.FULL
    )
    assert validation_request == same_request
    assert validation_request != different_input
    assert validation_request != different_format
    assert validation_request != different_mode
    assert validation_request == validation_request

    