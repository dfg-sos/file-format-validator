import pytest
from pathlib import Path
from format_validator import ValidationRequest, ValidationMode, FileInput, FormatIdentifier, UnsupportedMode

@pytest.fixture
def validation_request():
    return ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.METADATA
    )

def test_enabled_modes(validation_request):
    assert validation_request.enabled_modes() == [ValidationMode.BASIC, ValidationMode.METADATA, ValidationMode.CONTENT]

def test_equality(validation_request):
    same_request = ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.METADATA
    )
    different_input = ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("different.txt")),
        mode=ValidationMode.METADATA
    )
    different_format = ValidationRequest(
        format_identifier=FormatIdentifier.GEOTIFF,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.METADATA
    )

    different_mode = ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.CONTENT
    )
    assert validation_request == same_request
    assert validation_request != different_input
    assert validation_request != different_format
    assert validation_request != different_mode
    assert validation_request == validation_request

    
class BasicOnlyRequest(ValidationRequest):
    def enabled_modes(self) -> list[ValidationMode]:
        return [ValidationMode.BASIC]

def test_enabled_mode_of_subclass():
    request = BasicOnlyRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.BASIC,
    )
    assert request.mode == ValidationMode.BASIC

@pytest.mark.parametrize("mode", [ValidationMode.METADATA, ValidationMode.CONTENT])
def test_mode_not_enabled_by_subclass(mode):
    with pytest.raises(UnsupportedMode):
        BasicOnlyRequest(
            format_identifier=FormatIdentifier.GIS,
            actual_file=FileInput(path=Path("test.txt")),
            mode=mode,
        )
