import pytest
import datetime
from pathlib import Path

from format_validator import (
    ValidationRequest,
    ValidationResult,
    ValidationMode,
    FormatIdentifier,
    FileInput,
    Info,
    Warning,
    Error,
    Severity,
    Cause,
)
from format_validator.model.validation_result import ValidationStatus


@pytest.fixture
def validation_request():
    return ValidationRequest(
        format_identifier=FormatIdentifier.GIS,
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.STRUCTURAL,
    )


@pytest.fixture
def info():
    return Info(message="Test info message")


@pytest.fixture
def warning():
    return Warning(message="Test warning message", cause=Cause.UNKNOWN)


@pytest.fixture
def error():
    return Error(message="Test error message", cause=Cause.FILE_OPEN_ERROR)


@pytest.fixture
def validation_result(validation_request):
    return ValidationResult(validation_request)


def test_event():
    event = Info(message="Test message")
    assert event.message == "Test message"
    assert event.severity() == Severity.INFO
    assert isinstance(event.timestamp, datetime.datetime)
    assert event.timestamp - datetime.datetime.now() < datetime.timedelta(seconds=1)
    timed_event = Warning(message="Timed event", timestamp=datetime.datetime(2024, 1, 1))
    assert timed_event.timestamp == datetime.datetime(2024, 1, 1)
    assert timed_event.severity() == Severity.WARNING
    assert timed_event.message == "Timed event"
    error_event = Error(message="Error event", cause=Cause.FILE_OPEN_ERROR)
    assert error_event.severity() == Severity.ERROR
    assert error_event.cause == Cause.FILE_OPEN_ERROR
    assert error_event.message == "Error event"
    assert error_event.timestamp - datetime.datetime.now() < datetime.timedelta(seconds=1)


def test_init(validation_request):
    result = ValidationResult(validation_request)
    assert result.events == []
    assert result.status == ValidationStatus.SUCCESS
    assert result.request == validation_request


def test_status(validation_result):
    assert validation_result.status == ValidationStatus.SUCCESS
    validation_result.status = ValidationStatus.SUCCESS
    assert validation_result.status == ValidationStatus.SUCCESS
    validation_result.status = ValidationStatus.UNCERTAIN
    assert validation_result.status == ValidationStatus.UNCERTAIN
    validation_result.status = ValidationStatus.SUCCESS
    assert validation_result.status == ValidationStatus.SUCCESS
    validation_result.status = ValidationStatus.FAILURE
    assert validation_result.status == ValidationStatus.FAILURE
    validation_result.status = ValidationStatus.UNCERTAIN
    assert validation_result.status == ValidationStatus.FAILURE
    validation_result.status = ValidationStatus.SUCCESS
    assert validation_result.status == ValidationStatus.FAILURE


def test_add_event(validation_result, info, warning, error):
    assert len(validation_result.events) == 0
    assert len(validation_result.get(Severity.INFO)) == 0
    assert len(validation_result.get(Severity.WARNING)) == 0
    assert len(validation_result.get(Severity.ERROR)) == 0
    assert validation_result.errors() == []
    assert validation_result.warnings() == []
    assert validation_result.infos() == []
    validation_result.add(info)
    assert len(validation_result.events) == 1
    assert validation_result.infos() == [info] == validation_result.get(Severity.INFO)
    assert validation_result.status == ValidationStatus.SUCCESS
    validation_result.add(warning)
    assert len(validation_result.events) == 2
    assert (
        validation_result.warnings() == [warning] == validation_result.get(Severity.WARNING)
    )
    assert validation_result.status == ValidationStatus.UNCERTAIN
    validation_result.add(error)
    assert len(validation_result.events) == 3
    assert validation_result.errors() == [error] == validation_result.get(Severity.ERROR)
    assert validation_result.status == ValidationStatus.FAILURE
    another_info = Info(message="Another info")
    validation_result.add(another_info)
    assert len(validation_result.events) == 4
    assert (
        validation_result.infos() == [info, another_info]
        == validation_result.get(Severity.INFO)
    )
    assert validation_result.status == ValidationStatus.FAILURE


class TestEmptyResult:
    def test_empty_result_is_valid(self, validation_request):
        result = ValidationResult(_request=validation_request)
        assert result.status == ValidationStatus.SUCCESS
        assert len(result.errors()) == 0
        assert len(result.warnings()) == 0
        assert len(result.infos()) == 0

    def test_empty_result_bool(self, validation_request):
        result = ValidationResult(_request=validation_request)
        assert bool(result)


class TestSuccess:
    def test_set_success(self, validation_request):
        result = ValidationResult.success(validation_request, Info(message="OK"))
        assert result.status == ValidationStatus.SUCCESS
        assert len(result.infos()) == 1
        assert result.infos()[0].message == "OK"
        assert bool(result)

    def test_set_success_without_info(self, validation_request):
        result = ValidationResult.success(validation_request)
        assert result.status == ValidationStatus.SUCCESS
        assert len(result.infos()) == 0


class TestFailure:
    def test_set_failure(self, validation_request):
        result = ValidationResult.failure(
            validation_request, Error(message="Bad", cause=Cause.UNKNOWN)
        )
        assert result.status == ValidationStatus.FAILURE
        assert len(result.errors()) == 1
        assert not bool(result)


class TestUncertainty:
    def test_set_uncertainty(self, validation_request):
        result = ValidationResult.uncertain(
            validation_request, Warning(message="Hmm", cause=Cause.UNKNOWN)
        )
        assert result.status == ValidationStatus.UNCERTAIN
        assert len(result.warnings()) == 1
        assert bool(result) is False


class TestAddEvent:
    def test_add_error_makes_failure(self, validation_request):
        result = ValidationResult(_request=validation_request)
        result.add(Error(message="E", cause=Cause.UNKNOWN))
        assert result.status == ValidationStatus.FAILURE

    def test_add_warning_makes_uncertain(self, validation_request):
        result = ValidationResult(_request=validation_request)
        result.add(Warning(message="W", cause=Cause.UNKNOWN))
        assert result.status == ValidationStatus.UNCERTAIN

    def test_add_info_keeps_success(self, validation_request):
        result = ValidationResult(_request=validation_request)
        result.add(Info(message="I"))
        assert result.status == ValidationStatus.SUCCESS

    def test_error_overrides_warning(self, validation_request):
        result = ValidationResult(_request=validation_request)
        result.add(Warning(message="W", cause=Cause.UNKNOWN))
        result.add(Error(message="E", cause=Cause.UNKNOWN))
        assert result.status == ValidationStatus.FAILURE


class TestMerge:
    def test_merge_combines_events(self, validation_request):
        r1 = ValidationResult.success(validation_request, Info(message="A"))
        r2 = ValidationResult.failure(
            validation_request, Error(message="B", cause=Cause.UNKNOWN)
        )
        merged = r1.merge(r2)
        assert merged.status == ValidationStatus.FAILURE
        assert len(merged.infos()) == 1
        assert len(merged.errors()) == 1

    def test_merge_with_none_returns_self(self, validation_request):
        r1 = ValidationResult.success(validation_request)
        assert r1.merge(None) is r1

    def test_merge_add_operator(self, validation_request):
        r1 = ValidationResult.success(validation_request, Info(message="A"))
        r2 = ValidationResult.failure(
            validation_request, Error(message="B", cause=Cause.UNKNOWN)
        )
        merged = r1 + r2
        assert merged.status == ValidationStatus.FAILURE

    def test_merge_different_requests_raises(self):
        req1 = ValidationRequest(
            format_identifier=FormatIdentifier.GEOTIFF,
            actual_file=FileInput(path=Path("a.txt")),
            mode=ValidationMode.BASIC,
        )
        req2 = ValidationRequest(
            format_identifier=FormatIdentifier.KML,
            actual_file=FileInput(path=Path("b.txt")),
            mode=ValidationMode.BASIC,
        )
        r1 = ValidationResult.success(req1)
        r2 = ValidationResult.success(req2)
        with pytest.raises(ValueError, match="Cannot merge"):
            r1.merge(r2)


class TestGetBySeverity:
    def test_get_filters_correctly(self, validation_request):
        result = ValidationResult(_request=validation_request)
        result.add(Info(message="i1"))
        result.add(Warning(message="w1", cause=Cause.UNKNOWN))
        result.add(Error(message="e1", cause=Cause.UNKNOWN))
        assert len(result.get(Severity.INFO)) == 1
        assert len(result.get(Severity.WARNING)) == 1
        assert len(result.get(Severity.ERROR)) == 1
