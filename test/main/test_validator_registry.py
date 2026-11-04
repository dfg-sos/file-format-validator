"""Tests for the validator registry."""
from typing import List
import pytest
from format_validator.model import (
    FileFormatValidator,
    FormatIdentifier,
    ValidationRequest,
    ValidationResult,
)
from format_validator.registry import registry, _Registry
from test.dummy_formats import BASE, REFINED, OTHER, NESTED


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
        registry.register(BASE)(DummyValidator)
        assert registry.get_registered_identifiers() == [BASE]
        assert registry.get_identifier_for_validator(DummyValidator) == BASE

    def test_get_validator_class(self):
        registry.register(BASE)(DummyValidator)
        assert registry.get_validator_class(BASE) is DummyValidator
        assert registry.get_validator_class(FormatIdentifier("test_unsupported")) is None

    def test_duplicate_identifier_raises(self):
        registry.register(BASE)(DummyValidator)
        with pytest.raises(KeyError, match="already registered"):
            registry.register(BASE)(AnotherDummyValidator)

    def test_duplicate_class_raises(self):
        registry.register(BASE)(DummyValidator)
        with pytest.raises(KeyError, match="already registered"):
            registry.register(REFINED)(DummyValidator)

    @pytest.mark.parametrize("identifier", [BASE, REFINED, OTHER, NESTED])
    def test_various_identifier_formats(self, identifier):
        registry.register(identifier)(DummyValidator)
        assert identifier in registry.get_registered_identifiers()

    def test_empty_identifier_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            registry.register(FormatIdentifier(""))(DummyValidator)


@pytest.mark.usefixtures("reset_registry")
class TestRegistryClass:
    def test_fresh_registry_instance(self):
        """A brand-new _Registry starts empty."""
        fresh = _Registry()
        assert fresh.get_registered_identifiers() == []
        assert fresh.get_validator_class(FormatIdentifier("test_unsupported")) is None
