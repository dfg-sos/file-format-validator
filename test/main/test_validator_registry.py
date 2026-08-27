"""Tests for the validator registry."""
from pathlib import Path
from typing import List
import pytest
from format_validator.model import (
    FileFormatValidator,
    FileInput,
    FormatIdentifier,
    ValidationRequest,
    ValidationResult,
    ValidationMode,
)
from format_validator.registry import registry, _Registry


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
        registry.register("geotiff")(DummyValidator)
        assert registry.get_registered_identifiers() == [FormatIdentifier("geotiff")]
        assert registry.get_identifier_for_validator(DummyValidator) == FormatIdentifier("geotiff")

    def test_choose_and_instantiate_success(self):
        registry.register("geotiff")(DummyValidator)
        request = ValidationRequest(
            format_identifier=FormatIdentifier("geotiff"),
            actual_file=FileInput(path=Path("x.dummy")),
            mode=ValidationMode.BASIC,
        )
        instance = registry.choose_and_instantiate(request)
        assert isinstance(instance, DummyValidator)

    def test_choose_and_instantiate_none(self):
        request = ValidationRequest(
            format_identifier=FormatIdentifier("test_unsupported"),
            actual_file=FileInput(path=Path("x.dummy")),
            mode=ValidationMode.BASIC,
        )
        assert registry.choose_and_instantiate(request) is None

    def test_duplicate_identifier_raises(self):
        registry.register("geotiff")(DummyValidator)
        with pytest.raises(KeyError, match="already registered"):
            registry.register("geotiff")(AnotherDummyValidator)

    def test_duplicate_class_raises(self):
        registry.register("geotiff")(DummyValidator)
        with pytest.raises(KeyError, match="already registered"):
            registry.register("cog")(DummyValidator)

    @pytest.mark.parametrize(
        "identifier",
        [
            "cog",
            "geojson",
            "shapefile",
            "geopackage",
            "netcdf",
            "grib",
            "gml",
        ],
    )
    def test_various_identifier_formats(self, identifier):
        registry.register(identifier)(DummyValidator)
        assert FormatIdentifier(identifier) in registry.get_registered_identifiers()

    def test_empty_identifier_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            registry.register("")(DummyValidator)

    def test_whitespace_identifier_stripped(self):
        registry.register("  geotiff  ")(DummyValidator)
        assert FormatIdentifier("geotiff") in registry.get_registered_identifiers()


class TestModuleLevelRegistry:
    def test_module_level_registry_has_defaults(self):
        """
        The module-level registry must contain the production validators
        without relying on any prior test imports.  We spawn a fresh
        subprocess so that validator test modules (which import concrete
        validators and trigger their decorators as a side effect) do not
        pollute the state.
        """
        import subprocess
        import sys

        code = (
            "from format_validator.registry import registry; "
            "from format_validator.model.format_identifier import FormatIdentifier; "
            "ids = registry.get_registered_identifiers(); "
            "assert len(ids) >= 15, f'Registry under-populated: {ids}'; "
            "assert FormatIdentifier('cog') in ids, 'Missing COG validator'; "
            "assert FormatIdentifier('geotiff') in ids, 'Missing GeoTIFF validator'; "
            "print('registry_ok')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(
                f"Registry not correctly initialised in fresh process.\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )


@pytest.mark.usefixtures("reset_registry")
class TestRegistryClass:
    def test_fresh_registry_instance(self):
        """A brand-new _Registry starts empty."""
        fresh = _Registry()
        assert fresh.get_registered_identifiers() == []
        assert fresh.choose_and_instantiate(
            ValidationRequest(
                format_identifier=FormatIdentifier("test_unsupported"),
                actual_file=FileInput(path=Path("a")),
                mode=ValidationMode.BASIC,
            )
        ) is None
