from typing import List, Optional

import pytest

from eo_format_validator.model.file_format_validator import FileFormatValidator
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.validator_registry import Registry
from eo_format_validator.model.validation_result import ValidationResult


class MockFileFormatValidator(FileFormatValidator):

    def _get_extensions(self) -> List[str]:
        pass

    def _validate_open(self, file_format: Format, file_input: FileInput,
                       validation_result: ValidationResult) -> ValidationResult:
        pass

    def _validate_crs(self, file_format: Format, file_input: FileInput,
                      validation_result: ValidationResult) -> ValidationResult:
        pass

class MockFileFormatValidator1(MockFileFormatValidator):

    pass

class MockFileFormatValidator2(MockFileFormatValidator):

    pass


def test_register_duplicate_identifier_raises_error():
    registry = Registry()
    reg1 = registry.register("format_test")
    reg1(MockFileFormatValidator)
    reg2 = registry.register("format_test")

    with pytest.raises(KeyError):
        reg2(MockFileFormatValidator)

def test_register_duplicate_cls_raises_error():
    registry = Registry()
    reg1 = registry.register("format_test")
    reg1(MockFileFormatValidator)
    reg2 = registry.register("format_test2")

    with pytest.raises(KeyError):
        reg2(MockFileFormatValidator)

def test_register_normal_correct():
    registry = Registry()
    reg1 = registry.register("format_test")
    reg1(MockFileFormatValidator)

    identifiers: List[str] = registry.get_registered_identifiers()
    assert identifiers == ["format_test"]

    reg_id: Optional[str]=registry.get_identifier_for_validator(MockFileFormatValidator)
    assert reg_id == "format_test"


@pytest.mark.parametrize("identifier", [
    "simple",
    "with-dash",
    "CAPS",
    "with_underscore",
    "format_webprotege_012",
    "format_4103",
    "1234"
])
def test_various_identifier_formats(identifier):
    registry = Registry()
    @registry.register(identifier)
    class TestValidator(MockFileFormatValidator):
        pass

    assert identifier in registry.get_registered_identifiers()

def test_choose_and_instantiate_correct_return():
    """Verify that choose_and_instantiate returns the correct class."""
    registry = Registry()
    reg1 = registry.register("format_test")
    reg1(MockFileFormatValidator1)
    reg2 = registry.register("format_test2")
    reg2(MockFileFormatValidator2)
    format_test = Format("format_test")
    format_test2 = Format("format_test2")
    format_foo = Format("format_foo")
    assert isinstance(registry.choose_and_instantiate(format_test), MockFileFormatValidator1)
    assert isinstance(registry.choose_and_instantiate(format_test2), MockFileFormatValidator2)
    assert registry.choose_and_instantiate(format_foo) is None


def test_multiple_registries_are_independent():
    """Verify different Registry instances don't interfere."""
    registry1 = Registry()
    registry2 = Registry()

    @registry1.register("test_id")
    class TestValidator(MockFileFormatValidator):
        pass

    assert "test_id" not in registry2.get_registered_identifiers()
