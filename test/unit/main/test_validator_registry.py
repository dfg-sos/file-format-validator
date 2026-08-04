"""Tests for the validator registry."""
from pathlib import Path
from typing import List
import pytest
from eo_format_validator.model import (
    FileFormatValidator,
    FileInput,
    ValidationRequest,
    ValidationResult,
    ValidationMode,
)
from eo_format_validator.registry import registry, _Registry


class DummyValidator(FileFormatValidator):
    """Minimal concrete validator for testing registration."""

    def get_extensions(self) -> List[str]:
        return [".dummy"]

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        return ValidationResult.success(request)


class AnotherDummyValidator(FileFormatValidator):
    def get_extensions(self) -> List[str]:
        return [".another"]

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        return ValidationResult.success(request)


@pytest.fixture
def reset_registry():
    """Clear the module-level registry before each test and restore after."""
    original_id = dict(registry._id_to_validators)
    original_cls = dict(registry._validators_to_id)
    registry._id_to_validators.clear()
    registry._validators_to_id.clear()
    yield
    registry._id_to_validators.clear()
    registry._validators_to_id.clear()
    registry._id_to_validators.update(original_id)
    registry._validators_to_id.update(original_cls)


@pytest.mark.usefixtures("reset_registry")
class TestRegistration:
    def test_register_and_retrieve(self):
        registry.register("fmt_1")(DummyValidator)
        assert registry.get_registered_identifiers() == ["fmt_1"]
        assert registry.get_identifier_for_validator(DummyValidator) == "fmt_1"

    def test_choose_and_instantiate_success(self):
        registry.register("fmt_1")(DummyValidator)
        request = ValidationRequest(
            format_identifier="fmt_1",
            actual_file=FileInput(path=Path("x.dummy")),
            mode=ValidationMode.BASIC,
        )
        instance = registry.choose_and_instantiate(request)
        assert isinstance(instance, DummyValidator)

    def test_choose_and_instantiate_none(self):
        request = ValidationRequest(
            format_identifier="unknown",
            actual_file=FileInput(path=Path("x.dummy")),
            mode=ValidationMode.BASIC,
        )
        assert registry.choose_and_instantiate(request) is None

    def test_duplicate_identifier_raises(self):
        registry.register("fmt_1")(DummyValidator)
        with pytest.raises(KeyError, match="already registered"):
            registry.register("fmt_1")(AnotherDummyValidator)

    def test_duplicate_class_raises(self):
        registry.register("fmt_1")(DummyValidator)
        with pytest.raises(KeyError, match="already registered"):
            registry.register("fmt_2")(DummyValidator)

    @pytest.mark.parametrize(
        "identifier",
        [
            "simple",
            "with-dash",
            "CAPS",
            "with_underscore",
            "format_webprotege_012",
            "format_4103",
            "1234",
        ],
    )
    def test_various_identifier_formats(self, identifier):
        registry.register(identifier)(DummyValidator)
        assert identifier in registry.get_registered_identifiers()

    def test_empty_identifier_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            registry.register("")(DummyValidator)

    def test_whitespace_identifier_stripped(self):
        registry.register("  fmt_1  ")(DummyValidator)
        assert "fmt_1" in registry.get_registered_identifiers()


class TestModuleLevelRegistry:
    def test_module_level_registry_has_defaults(self):
        """The real module-level registry should contain the production validators."""
        # This test runs after reset_registry restores the original state
        identifiers = registry.get_registered_identifiers()
        assert len(identifiers) >= 15
        assert "format_4100" in identifiers  # COG
        assert "format_4109" in identifiers  # GeoTIFF


@pytest.mark.usefixtures("reset_registry")
class TestRegistryClass:
    def test_fresh_registry_instance(self):
        """A brand-new _Registry starts empty."""
        fresh = _Registry()
        assert fresh.get_registered_identifiers() == []
        assert fresh.choose_and_instantiate(
            ValidationRequest(
                format_identifier="x",
                actual_file=FileInput(path=Path("a")),
                mode=ValidationMode.BASIC,
            )
        ) is None
