"""Tests for validating against abstract formats, which cover all their leaves."""
from pathlib import Path
import pytest

from format_validator import (
    FormatIdentifier,
    FileInput,
    ValidationMode,
    ValidationResult,
    ValidationStatus,
    UnsupportedMetadataKeys,
    Cause,
    build_request,
    metadata_keys,
    validate,
)
from format_validator.model import (
    FileFormatValidator,
    Warning,
    Error,
)
from format_validator.validators import EOMetadata
from format_validator.registry import _Registry
from test.fixtures import geotiff_input, geotiff_no_cog_input, geojson_input, wgs84_crs


def parse(identifier: FormatIdentifier, values) -> object:
    """The metadata object ``build_request`` builds from plain strings."""
    return build_request(identifier, FileInput(path=Path("file")), ValidationMode.BASIC, values).metadata


class TestAbstractFormats:
    @pytest.mark.parametrize("identifier", [FormatIdentifier.RASTER, FormatIdentifier.GIS])
    def test_valid_for_a_leaf(self, geotiff_input, identifier):
        result = validate(build_request(identifier, geotiff_input, ValidationMode.FULL))
        assert result.status == ValidationStatus.SUCCESS
        assert any(f"a format of '{identifier}'" in info.message for info in result.infos())

    @pytest.mark.parametrize("mode", list(ValidationMode))
    def test_extension_of_no_leaf(self, geotiff_input, mode):
        result = validate(build_request(FormatIdentifier.VECTOR, geotiff_input, mode))
        assert result.status == ValidationStatus.FAILURE
        assert [error.cause for error in result.errors()] == [Cause.EXTENSION_MISMATCH]

    def test_invalid_for_all_leaves(self, geotiff_no_cog_input):
        # The file's CRS is EPSG:32617
        result = validate(
            build_request(FormatIdentifier.RASTER, geotiff_no_cog_input, ValidationMode.FULL, {"crs": "EPSG:4326"})
        )
        assert result.status == ValidationStatus.FAILURE
        assert any(error.cause == Cause.METADATA_MISMATCH for error in result.errors())
        assert any(info.message.startswith("Validated as 'GeoTIFF'") for info in result.infos())

    def test_metadata_mismatch_for_vector(self, geojson_input):
        result = validate(
            build_request(FormatIdentifier.VECTOR, geojson_input, ValidationMode.FULL, {"geometry_type": "Point"})
        )
        assert result.status == ValidationStatus.FAILURE


class TestAbstractMetadata:
    @pytest.mark.parametrize(
        "identifier, keys",
        [
            (FormatIdentifier.GIS, {"crs"}),
            (FormatIdentifier.RASTER, {"crs"}),
            (FormatIdentifier.VECTOR, {"crs", "geometry_type"}),
        ],
    )
    def test_keys_shared_by_all_leaves(self, identifier, keys):
        assert metadata_keys(identifier) == keys

    def test_parse(self, wgs84_crs):
        assert parse(FormatIdentifier.RASTER, {"crs": "EPSG:4326"}) == EOMetadata(crs=wgs84_crs)

    def test_key_not_shared_by_all_leaves(self):
        with pytest.raises(UnsupportedMetadataKeys):
            parse(FormatIdentifier.GIS, {"geometry_type": "Point"})


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
        return validate(build_request(ABSTRACT, FileInput(path=Path("file.dummy")), ValidationMode.FULL))

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
