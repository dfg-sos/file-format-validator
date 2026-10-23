"""Tests for the module-level API: supported_formats, metadata_keys, build_request and validate."""
from pathlib import Path
import pytest

from format_validator import (
    FormatIdentifier,
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
    ValidationMode,
    FileInput,
    InvalidRequest,
    UnsupportedFormat,
    build_request,
    metadata_keys,
    supported_formats,
    validate,
)
from format_validator.model import FileFormatValidator
from format_validator.registry import registry, _Registry


class DummyValidator(FileFormatValidator):
    """A validator that always succeeds for testing."""

    def get_extensions(self):
        return [".dummy"]

    def assert_can_open(self, request):
        return ValidationResult.success(request)


UNREGISTERED = FormatIdentifier("test_unsupported")


@pytest.fixture
def dummy_request():
    return ValidationRequest(
        format_identifier=FormatIdentifier("geotiff"),
        actual_file=FileInput(path=Path("file.dummy")),
        mode=ValidationMode.BASIC,
    )


@pytest.fixture
def isolated_registry(monkeypatch):
    """Replace the registry used by the API with a fresh empty one."""
    fresh = _Registry()
    monkeypatch.setattr("format_validator.validator.registry", fresh)
    return fresh


class TestSupportedFormats:
    def test_registered_formats(self):
        assert set(registry.get_registered_identifiers()) <= set(supported_formats())

    @pytest.mark.parametrize("identifier", [FormatIdentifier.GIS, FormatIdentifier.RASTER, FormatIdentifier.VECTOR])
    def test_abstract_formats(self, identifier):
        assert identifier in supported_formats()

    def test_format_without_validator(self):
        assert FormatIdentifier.CSV not in supported_formats()

    def test_abstract_format_without_leaf_validators(self, isolated_registry):
        assert supported_formats() == []

    def test_sorted(self):
        formats = supported_formats()
        assert formats == sorted(formats)


class TestValidate:
    def test_successful_validation(self, isolated_registry, dummy_request):
        isolated_registry.register("geotiff")(DummyValidator)
        result = validate(dummy_request)
        assert result.status == ValidationStatus.SUCCESS

    def test_unsupported_format_raises(self):
        request = ValidationRequest(
            format_identifier=UNREGISTERED,
            actual_file=FileInput(path=Path("file.dummy")),
            mode=ValidationMode.BASIC,
        )
        with pytest.raises(UnsupportedFormat) as exc_info:
            validate(request)
        assert exc_info.value.format_identifier == UNREGISTERED

    def test_exception_during_validation(self, isolated_registry):
        class BrokenValidator(FileFormatValidator):
            def get_extensions(self):
                return [".dummy"]

            def assert_can_open(self, request):
                raise RuntimeError("boom")

        isolated_registry.register("geotiff")(BrokenValidator)
        dummy_request_full = ValidationRequest(
            format_identifier=FormatIdentifier("geotiff"),
            actual_file=FileInput(path=Path("file.dummy")),
            mode=ValidationMode.FULL,
        )
        result = validate(dummy_request_full)
        assert result.status == ValidationStatus.UNCERTAIN
        assert len(result.warnings()) == 1
        assert "exception during validation" in result.warnings()[0].message.lower()

    def test_validate_with_real_geotiff(self):
        request = ValidationRequest(
            format_identifier=FormatIdentifier("geotiff"),
            actual_file=FileInput(path=Path("test/data/o41078a2.tif")),
            mode=ValidationMode.STRUCTURAL,
        )
        assert validate(request).status == ValidationStatus.SUCCESS


class TestRequest:
    def test_unsupported_format_raises(self):
        with pytest.raises(UnsupportedFormat) as exc_info:
            build_request(UNREGISTERED, FileInput(path=Path("file.dummy")), ValidationMode.BASIC)
        assert isinstance(exc_info.value, InvalidRequest)

    def test_unsupported_format_with_metadata_raises_unsupported_format(self):
        with pytest.raises(UnsupportedFormat):
            build_request(UNREGISTERED, FileInput(path=Path("file.dummy")), ValidationMode.BASIC, {"crs": "EPSG:4326"})

    def test_metadata_keys_of_unsupported_format(self):
        assert metadata_keys(UNREGISTERED) == frozenset()

    def test_real_registry_has_cog(self):
        assert FormatIdentifier("cog") in registry.get_registered_identifiers()
