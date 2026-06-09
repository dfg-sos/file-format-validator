import pytest
import datetime
from pathlib import Path

from eo_format_validator import ValidationRequest,ValidationResult, ValidationMode, FileInput,Info, Warning, Error,Severity,Cause
from eo_format_validator.model.validation_result import ValidationStatus

@pytest.fixture
def validation_request():
    return ValidationRequest(
        format_identifier="test_format",
        actual_file=FileInput(path=Path("test.txt")),
        mode=ValidationMode.STRUCTURAL
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
    assert validation_result.warnings() == [warning] == validation_result.get(Severity.WARNING)
    assert validation_result.status == ValidationStatus.UNCERTAIN # Warning sets status to uncertain if there was no set_success before
    validation_result.add(error)
    assert len(validation_result.events) == 3
    assert validation_result.errors() == [error] == validation_result.get(Severity.ERROR)
    assert validation_result.status == ValidationStatus.FAILURE
    another_info = Info(message="Another info")
    validation_result.add(another_info)
    assert len(validation_result.events) == 4
    assert validation_result.infos() == [info, another_info] == validation_result.get(Severity.INFO)
    assert validation_result.status == ValidationStatus.FAILURE