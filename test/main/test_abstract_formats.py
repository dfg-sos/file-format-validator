"""Tests for validating against abstract formats, with dummy formats and validators."""
from pathlib import Path
import pytest

from format_validator import (
    FormatIdentifier,
    FileInput,
    ValidationMode,
    ValidationResult,
    ValidationStatus,
    Cause,
    build_request,
    validate,
)
from format_validator.model import FileFormatValidator, Warning, Error
from format_validator.registry import _Registry
from format_validator.validator import _validated_leaves
from test.dummy_formats import GROUP, BASE, REFINED, OTHER, INNER, NESTED


ABSTRACT = FormatIdentifier("test_abstract", children_ids=["test_leaf_a", "test_leaf_b"], is_abstract=True)
LEAF_A = FormatIdentifier("test_leaf_a")
LEAF_B = FormatIdentifier("test_leaf_b")


def dummy_validator(status: ValidationStatus) -> type[FileFormatValidator]:
    class DummyValidator(FileFormatValidator):
        def get_extensions(self):
            return [".dummy"]

        def assert_can_open(self, request):
            return ValidationResult.success(request)

        def validate(self, request):
            match status:
                case ValidationStatus.SUCCESS:
                    return ValidationResult.success(request)
                case ValidationStatus.UNCERTAIN:
                    return ValidationResult.uncertain(request, Warning(message="uncertain", cause=Cause.UNKNOWN))
                case _:
                    return ValidationResult.failure(request, Error(message="failure", cause=Cause.FILE_OPEN_ERROR))

    return DummyValidator


class TestAbstractResult:
    @pytest.fixture
    def register(self, monkeypatch):
        fresh = _Registry()
        monkeypatch.setattr("format_validator.validator.registry", fresh)

        def register(status_a: ValidationStatus, status_b: ValidationStatus):
            fresh.register(LEAF_A)(dummy_validator(status_a))
            fresh.register(LEAF_B)(dummy_validator(status_b))

        return register

    def validate_abstract(self) -> ValidationResult:
        return validate(build_request(ABSTRACT, FileInput(path=Path("file.dummy")), ValidationMode.METADATA))

    @pytest.mark.parametrize(
        "status_a, status_b, expected",
        [
            (ValidationStatus.FAILURE, ValidationStatus.SUCCESS, ValidationStatus.SUCCESS),
            (ValidationStatus.FAILURE, ValidationStatus.UNCERTAIN, ValidationStatus.UNCERTAIN),
            (ValidationStatus.FAILURE, ValidationStatus.FAILURE, ValidationStatus.FAILURE),
        ],
    )
    def test_status(self, register, status_a, status_b, expected):
        register(status_a, status_b)
        assert self.validate_abstract().status == expected

    def test_success_keeps_only_the_valid_leaf(self, register):
        register(ValidationStatus.FAILURE, ValidationStatus.SUCCESS)
        result = self.validate_abstract()
        assert result.errors() == []
        assert result.infos()[-1].message == "File is valid as 'test_leaf_b', a format of 'test_abstract'."

    def test_uncertain_keeps_only_uncertain_leaves(self, register):
        register(ValidationStatus.FAILURE, ValidationStatus.UNCERTAIN)
        result = self.validate_abstract()
        assert result.errors() == []
        assert [info.message for info in result.infos()] == ["Validated as 'test_leaf_b', a format of 'test_abstract':"]

    def test_failure_keeps_all_leaves(self, register):
        register(ValidationStatus.FAILURE, ValidationStatus.FAILURE)
        result = self.validate_abstract()
        assert [error.message for error in result.errors()] == ["failure", "failure"]


class TestMostGeneralLeaves:
    """An abstract format covers the most general formats with a validator below it."""

    @pytest.fixture
    def fresh(self, monkeypatch):
        fresh = _Registry()
        monkeypatch.setattr("format_validator.validator.registry", fresh)
        return fresh

    def test_stops_at_a_format_with_a_validator(self, fresh):
        fresh.register(BASE)(dummy_validator(ValidationStatus.SUCCESS))
        fresh.register(REFINED)(dummy_validator(ValidationStatus.SUCCESS))
        assert _validated_leaves(GROUP) == [BASE]

    def test_descends_below_a_format_without_validator(self, fresh):
        fresh.register(REFINED)(dummy_validator(ValidationStatus.SUCCESS))
        fresh.register(NESTED)(dummy_validator(ValidationStatus.SUCCESS))
        assert set(_validated_leaves(GROUP)) == {REFINED, NESTED}

    def test_format_below_two_parents_once(self, fresh):
        fresh.register(OTHER)(dummy_validator(ValidationStatus.SUCCESS))
        assert _validated_leaves(GROUP) == [OTHER]

    def test_concrete_format_covers_only_itself(self, fresh):
        fresh.register(REFINED)(dummy_validator(ValidationStatus.SUCCESS))
        assert _validated_leaves(BASE) == [BASE]

    def test_validator_of_several_formats_runs_once(self, fresh):
        calls = []

        class Shared(dummy_validator(ValidationStatus.FAILURE)):
            def validate(self, request):
                calls.append(request)
                return super().validate(request)

        fresh.register(OTHER, NESTED)(Shared)
        result = validate(build_request(INNER, FileInput(path=Path("file.dummy")), ValidationMode.METADATA))
        assert len(calls) == 1
        assert result.infos()[0].message == "Validated as 'test_other' (also 'test_nested'), a format of 'test_inner':"
