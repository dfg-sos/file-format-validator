"""Validating files against the abstract EO formats. The generic logic is tested in the core."""
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
from format_validator_eo import EOMetadata
from format_validator.registry import _Registry
from tests.fixtures import geotiff_input, geotiff_no_cog_input, geojson_input, wgs84_crs
from format_validator_eo import eo_formats


def parse(identifier: FormatIdentifier, values) -> object:
    """The metadata object ``build_request`` builds from plain strings."""
    return build_request(identifier, FileInput(path=Path("file")), ValidationMode.BASIC, values).metadata


class TestAbstractFormats:
    @pytest.mark.parametrize("identifier", [eo_formats.RASTER, eo_formats.GIS])
    def test_valid_for_a_leaf(self, geotiff_input, identifier):
        result = validate(build_request(identifier, geotiff_input, ValidationMode.METADATA))
        assert result.status == ValidationStatus.SUCCESS
        assert any(f"a format of '{identifier}'" in info.message for info in result.infos())

    @pytest.mark.parametrize("mode", list(ValidationMode))
    def test_extension_of_no_leaf(self, geotiff_input, mode):
        result = validate(build_request(eo_formats.VECTOR, geotiff_input, mode))
        assert result.status == ValidationStatus.FAILURE
        assert [error.cause for error in result.errors()] == [Cause.EXTENSION_MISMATCH]

    def test_invalid_for_all_leaves(self, geotiff_no_cog_input):
        # The file's CRS is EPSG:32617
        result = validate(
            build_request(eo_formats.RASTER, geotiff_no_cog_input, ValidationMode.METADATA, {"crs": "EPSG:4326"})
        )
        assert result.status == ValidationStatus.FAILURE
        assert any(error.cause == Cause.METADATA_MISMATCH for error in result.errors())
        assert any(info.message.startswith("Validated as 'GeoTIFF'") for info in result.infos())

    def test_metadata_mismatch_for_vector(self, geojson_input):
        result = validate(
            build_request(eo_formats.VECTOR, geojson_input, ValidationMode.METADATA, {"geometry_type": "Point"})
        )
        assert result.status == ValidationStatus.FAILURE


class TestAbstractMetadata:
    @pytest.mark.parametrize(
        "identifier, keys",
        [
            (eo_formats.GIS, {"crs"}),
            (eo_formats.RASTER, {"crs"}),
            (eo_formats.VECTOR, {"crs", "geometry_type"}),
        ],
    )
    def test_keys_shared_by_all_leaves(self, identifier, keys):
        assert metadata_keys(identifier) == keys

    def test_parse(self, wgs84_crs):
        assert parse(eo_formats.RASTER, {"crs": "EPSG:4326"}) == EOMetadata(crs=wgs84_crs)

    def test_key_not_shared_by_all_leaves(self):
        with pytest.raises(UnsupportedMetadataKeys):
            parse(eo_formats.GIS, {"geometry_type": "Point"})


class TestAbstractContent:
    """The costly content read runs once for the leaves of one validator."""

    @pytest.fixture
    def reads(self, monkeypatch):
        from format_validator_eo.raster_file_validator import RasterFileValidator

        calls = []
        outcome = {"result": None}
        original = RasterFileValidator.assert_content

        def counting(validator, request):
            calls.append(type(validator).__name__)
            return outcome["result"](request) if outcome["result"] else original(validator, request)

        monkeypatch.setattr(RasterFileValidator, "assert_content", counting)
        return calls, outcome

    def test_stops_at_first_valid_leaf(self, geotiff_no_cog_input, reads):
        calls, _ = reads
        result = validate(build_request(eo_formats.RASTER, geotiff_no_cog_input, ValidationMode.CONTENT))
        assert result.status == ValidationStatus.SUCCESS
        assert len(calls) == 1

    def test_failed_read_is_not_repeated(self, geotiff_no_cog_input, reads):
        calls, outcome = reads
        outcome["result"] = lambda request: ValidationResult.failure(
            request, Error(message="corrupt", cause=Cause.STRUCTURAL_MALFORMED)
        )
        result = validate(build_request(eo_formats.RASTER, geotiff_no_cog_input, ValidationMode.CONTENT))
        assert result.status == ValidationStatus.FAILURE
        assert len(calls) == 1
        assert [error.message for error in result.errors()].count("corrupt") == 1


class TestAbstractSharedValidator:
    """Formats registered for one validator (GeoTIFF, DEM, DSM, DTM) are validated once."""

    def test_reports_all_formats_of_the_validator(self, geotiff_no_cog_input):
        result = validate(build_request(eo_formats.RASTER, geotiff_no_cog_input, ValidationMode.METADATA))
        assert result.status == ValidationStatus.SUCCESS
        assert result.infos()[-1].message == (
            "File is valid as 'GeoTIFF' (also 'DEM', 'DSM', 'DTM'), a format of 'GISRaster'."
        )

    @pytest.mark.parametrize("identifier", [eo_formats.DEM, eo_formats.DSM, eo_formats.DTM])
    def test_concrete_format_uses_the_shared_validator(self, geotiff_no_cog_input, identifier):
        result = validate(build_request(identifier, geotiff_no_cog_input, ValidationMode.METADATA))
        assert result.status == ValidationStatus.SUCCESS


class TestMostGeneralLeaves:
    """An abstract format covers the most general formats with a validator below it."""

    def test_refinement_is_not_validated(self):
        from format_validator.validator import _validated_leaves

        leaves = _validated_leaves(eo_formats.RASTER)
        assert eo_formats.GEOTIFF in leaves
        assert eo_formats.COG not in leaves

    def test_cog_is_valid_as_geotiff(self, geotiff_input):
        result = validate(build_request(eo_formats.RASTER, geotiff_input, ValidationMode.METADATA))
        assert result.infos()[-1].message.startswith("File is valid as 'GeoTIFF'")

    def test_children_refine_their_parent(self):
        # A file of a child must pass its parent's extension check, else the abstract format rejects it.
        from format_validator.registry import registry

        for parent in FormatIdentifier.all():
            parent_cls = registry.get_validator_class(parent)
            for child in parent.children:
                child_cls = registry.get_validator_class(child)
                if parent_cls and child_cls:
                    parent_ext = {ext.lower() for ext in parent_cls().get_extensions()}
                    child_ext = {ext.lower() for ext in child_cls().get_extensions()}
                    assert child_ext <= parent_ext, f"{child} accepts extensions that {parent} does not"
