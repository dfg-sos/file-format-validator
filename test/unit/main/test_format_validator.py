"""Tests for the FormatValidator entrypoint."""
from pathlib import Path
from unittest.mock import create_autospec
import pytest
from eo_format_validator.format_validator import FormatValidator
from eo_format_validator.model import (
    ValidationRequestBuilder,
    ValidationResponseHandler,
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
    ValidationMode,
    FileInput,
    Warning,
    Error,
    Cause,
    FileFormatValidator,
)
from eo_format_validator.registry import registry, _Registry


class DummyValidator(FileFormatValidator):
    """A validator that always succeeds for testing."""

    def get_extensions(self):
        return [".dummy"]

    def assert_can_open(self, request):
        return ValidationResult.success(request)


@pytest.fixture
def dummy_request():
    return ValidationRequest(
        format_identifier="fmt_dummy",
        actual_file=FileInput(path=Path("file.dummy")),
        mode=ValidationMode.BASIC,
    )


@pytest.fixture
def mock_builder(dummy_request):
    builder = create_autospec(ValidationRequestBuilder, instance=True)
    builder.build.return_value = dummy_request
    return builder


@pytest.fixture
def mock_handler():
    handler = create_autospec(ValidationResponseHandler, instance=True)
    handler.handle_success.return_value = {"status": "success"}
    handler.handle_failure.return_value = {"status": "failure"}
    handler.handle_uncertain.return_value = {"status": "uncertain"}

    def real_handle(result):
        match result.status:
            case ValidationStatus.SUCCESS:
                return handler.handle_success(result)
            case ValidationStatus.FAILURE:
                return handler.handle_failure(result)
            case ValidationStatus.UNCERTAIN:
                return handler.handle_uncertain(result)

    handler.handle.side_effect = real_handle
    return handler


@pytest.fixture
def isolated_registry(monkeypatch):
    """Replace the registry used by the entrypoint with a fresh empty one."""
    fresh = _Registry()
    monkeypatch.setattr("eo_format_validator.format_validator.registry", fresh)
    return fresh


class TestValidateStatic:
    def test_successful_validation(self, isolated_registry, dummy_request):
        isolated_registry.register("fmt_dummy")(DummyValidator)
        result = FormatValidator.validate(dummy_request)
        assert result.status == ValidationStatus.SUCCESS

    def test_unsupported_format_returns_uncertain(self, dummy_request):
        result = FormatValidator.validate(dummy_request)
        assert result.status == ValidationStatus.UNCERTAIN
        assert len(result.warnings()) == 1
        assert "not supported" in result.warnings()[0].message.lower()

    def test_exception_during_validation(self, isolated_registry, dummy_request):
        class BrokenValidator(FileFormatValidator):
            def get_extensions(self):
                return [".dummy"]

            def assert_can_open(self, request):
                raise RuntimeError("boom")

        isolated_registry.register("fmt_dummy")(BrokenValidator)
        dummy_request_full = ValidationRequest(
            format_identifier="fmt_dummy",
            actual_file=FileInput(path=Path("file.dummy")),
            mode=ValidationMode.FULL,
        )
        result = FormatValidator.validate(dummy_request_full)
        assert result.status == ValidationStatus.UNCERTAIN
        assert len(result.warnings()) == 1
        assert "exception during validation" in result.warnings()[0].message.lower()


class TestRun:
    def test_run_success(self, isolated_registry, mock_builder, mock_handler):
        isolated_registry.register("fmt_dummy")(DummyValidator)
        eo = FormatValidator(mock_builder, mock_handler)
        response = eo.run()
        mock_builder.build.assert_called_once()
        mock_handler.handle.assert_called_once()
        args, _ = mock_handler.handle.call_args
        assert args[0].status == ValidationStatus.SUCCESS
        mock_handler.handle_success.assert_called_once()
        assert response == {"status": "success"}

    def test_run_failure(self, isolated_registry, mock_builder, mock_handler):
        class FailingValidator(FileFormatValidator):
            def get_extensions(self):
                return [".dummy"]

            def assert_can_open(self, request):
                return ValidationResult.failure(
                    request, Error(message="fail", cause=Cause.UNKNOWN)
                )

        isolated_registry.register("fmt_dummy")(FailingValidator)
        request = ValidationRequest(
            format_identifier="fmt_dummy",
            actual_file=FileInput(path=Path("file.dummy")),
            mode=ValidationMode.FULL,
        )
        mock_builder.build.return_value = request
        eo = FormatValidator(mock_builder, mock_handler)
        response = eo.run()
        mock_handler.handle.assert_called_once()
        args, _ = mock_handler.handle.call_args
        assert args[0].status == ValidationStatus.FAILURE
        mock_handler.handle_failure.assert_called_once()
        assert response == {"status": "failure"}

    def test_run_builder_returns_none(self, mock_builder, mock_handler):
        mock_builder.build.return_value = None
        eo = FormatValidator(mock_builder, mock_handler)
        response = eo.run()
        mock_handler.handle_uncertain.assert_called_once()
        assert response == {"status": "uncertain"}

    def test_run_validation_exception(self, isolated_registry, mock_builder, mock_handler):
        class BrokenValidator(FileFormatValidator):
            def get_extensions(self):
                return [".dummy"]

            def validate(self, request):
                raise RuntimeError("validation crashed")

        isolated_registry.register("fmt_dummy")(BrokenValidator)
        request = ValidationRequest(
            format_identifier="fmt_dummy",
            actual_file=FileInput(path=Path("file.dummy")),
            mode=ValidationMode.BASIC,
        )
        mock_builder.build.return_value = request
        eo = FormatValidator(mock_builder, mock_handler)
        response = eo.run()
        mock_handler.handle_uncertain.assert_called_once()
        args, _ = mock_handler.handle_uncertain.call_args
        assert args[0].status == ValidationStatus.UNCERTAIN
        assert response == {"status": "uncertain"}


class TestRunWithoutRegistryIsolation:
    """Integration-ish tests using the real module-level registry."""

    def test_real_registry_has_cog(self):
        assert "format_4100" in registry.get_registered_identifiers()

    def test_validate_with_real_geotiff(self):
        request = ValidationRequest(
            format_identifier="format_4109",
            actual_file=FileInput(path=Path("data/geo/o41078a2.tif")),
            mode=ValidationMode.STRUCTURAL,
        )
        result = FormatValidator.validate(request)
        assert result.status == ValidationStatus.SUCCESS
