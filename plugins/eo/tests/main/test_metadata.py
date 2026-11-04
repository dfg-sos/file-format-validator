"""Tests for parsing expected metadata from plain strings via the format's validator."""
from pathlib import Path
import pytest
from pyproj import CRS
from shapely import GeometryType

from format_validator import (
    FormatIdentifier,
    FileInput,
    ValidationRequest,
    ValidationMode,
    ValidationStatus,
    Cause,
    InvalidRequest,
    UnsupportedFormat,
    UnsupportedMetadataKeys,
    InvalidMetadataValue,
    build_request,
    metadata_keys,
    validate,
)
from format_validator_eo import EOMetadata
from tests.fixtures import geojson_input, geotiff_input, wgs84_crs
from format_validator_eo import formats


UNREGISTERED = FormatIdentifier("test_unregistered_metadata")


def parse(identifier: FormatIdentifier, values) -> object:
    """The metadata object ``build_request`` builds from plain strings."""
    return build_request(identifier, FileInput(path=Path("file")), ValidationMode.BASIC, values).metadata


class TestSupportedMetadataKeys:
    @pytest.mark.parametrize(
        "identifier",
        [formats.GEOJSON, formats.SHAPEFILE, formats.GEOPACKAGE],
    )
    def test_vector_formats(self, identifier):
        assert metadata_keys(identifier) == {"crs", "geometry_type"}

    @pytest.mark.parametrize("identifier", [formats.GEOTIFF, formats.COG])
    def test_raster_formats(self, identifier):
        assert metadata_keys(identifier) == {"crs"}

    def test_unregistered_format(self):
        assert metadata_keys(UNREGISTERED) == frozenset()


class TestParseMetadata:
    def test_valid_values(self):
        metadata = parse(
            formats.GEOJSON, {"crs": "EPSG:4326", "geometry_type": "Polygon"}
        )
        assert metadata == EOMetadata(crs=CRS.from_epsg(4326), geometry_type=GeometryType.POLYGON)

    def test_raster_crs(self):
        metadata = parse(formats.GEOTIFF, {"crs": "EPSG:4326"})
        assert metadata == EOMetadata(crs=CRS.from_epsg(4326))

    @pytest.mark.parametrize("values", [{}, {"crs": "", "geometry_type": ""}])
    def test_no_values_gives_empty_metadata(self, values):
        assert parse(formats.GEOJSON, values) == EOMetadata()

    def test_empty_value_for_unsupported_key_is_ignored(self):
        assert parse(formats.GEOTIFF, {"geometry_type": ""}) == EOMetadata()

    def test_unregistered_format_without_values(self):
        with pytest.raises(UnsupportedFormat):
            parse(UNREGISTERED, {})


class TestParseMetadataErrors:
    def test_unknown_key(self):
        with pytest.raises(UnsupportedMetadataKeys) as exc_info:
            parse(formats.GEOJSON, {"crs": "EPSG:4326", "foo": "bar"})
        assert exc_info.value.unknown == {"foo"}
        assert exc_info.value.supported == {"crs", "geometry_type"}

    def test_geometry_type_for_raster(self):
        with pytest.raises(UnsupportedMetadataKeys) as exc_info:
            parse(formats.GEOTIFF, {"geometry_type": "Polygon"})
        assert exc_info.value.unknown == {"geometry_type"}
        assert exc_info.value.supported == {"crs"}

    def test_key_for_unregistered_format(self):
        # Reported as an unsupported format, not as unsupported keys
        with pytest.raises(UnsupportedFormat):
            parse(UNREGISTERED, {"crs": "EPSG:4326"})

    @pytest.mark.parametrize(
        "values", [{"crs": "not-a-crs"}, {"geometry_type": "NotAGeometry"}], ids=["crs", "geometry_type"]
    )
    def test_invalid_value(self, values):
        with pytest.raises(InvalidMetadataValue) as exc_info:
            parse(formats.GEOJSON, values)
        assert exc_info.value.__cause__ is not None


class TestParsedMetadataValidation:
    def test_full_mode_matches_hand_built_metadata(self, geojson_input, wgs84_crs):
        def validate_with(metadata):
            return validate(
                ValidationRequest(
                    format_identifier=formats.GEOJSON,
                    actual_file=geojson_input,
                    mode=ValidationMode.METADATA,
                    metadata=metadata,
                )
            )

        parsed = parse(formats.GEOJSON, {"crs": "EPSG:4326"})
        expected = validate_with(EOMetadata(crs=wgs84_crs))
        actual = validate_with(parsed)
        assert actual.status == expected.status
        assert [e.message for e in actual.events] == [e.message for e in expected.events]


class TestUnsupportedMetadataType:
    @pytest.mark.parametrize("mode", list(ValidationMode))
    @pytest.mark.parametrize(
        "identifier, file_fixture",
        [(formats.GEOJSON, "geojson_input"), (formats.GEOTIFF, "geotiff_input")],
        ids=["vector", "raster"],
    )
    def test_raw_mapping_fails(self, identifier, file_fixture, mode, request):
        result = validate(
            ValidationRequest(
                format_identifier=identifier,
                actual_file=request.getfixturevalue(file_fixture),
                mode=mode,
                metadata={"crs": "EPSG:4326"},
            )
        )
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH and "dict" in err.message for err in result.errors())

    @pytest.mark.parametrize("mode", list(ValidationMode))
    def test_no_metadata_passes(self, geojson_input, mode):
        result = validate(
            ValidationRequest(format_identifier=formats.GEOJSON, actual_file=geojson_input, mode=mode)
        )
        assert result.status == ValidationStatus.SUCCESS


class TestRequest:
    def test_parses_metadata(self, geojson_input):
        request = build_request(formats.GEOJSON, geojson_input, ValidationMode.METADATA, {"crs": "EPSG:4326"})
        assert request == ValidationRequest(
            formats.GEOJSON, geojson_input, ValidationMode.METADATA, EOMetadata(crs=CRS.from_epsg(4326))
        )

    def test_no_metadata_gives_empty_metadata(self, geojson_input):
        assert build_request(formats.GEOJSON, geojson_input, ValidationMode.METADATA).metadata == EOMetadata()

    @pytest.mark.parametrize(
        "metadata, error",
        [({"foo": "bar"}, UnsupportedMetadataKeys), ({"crs": "not-a-crs"}, InvalidMetadataValue)],
        ids=["key", "value"],
    )
    def test_invalid_request(self, geojson_input, metadata, error):
        with pytest.raises(error) as exc_info:
            build_request(formats.GEOJSON, geojson_input, ValidationMode.METADATA, metadata)
        assert isinstance(exc_info.value, InvalidRequest)


class TestMissingMetadata:
    @pytest.mark.parametrize(
        "identifier, file_fixture",
        [(formats.GEOJSON, "geojson_input"), (formats.GEOTIFF, "geotiff_input")],
        ids=["vector", "raster"],
    )
    def test_none_reports_skipped_checks_like_empty_metadata(self, identifier, file_fixture, request):
        def validate_with(metadata):
            return validate(
                ValidationRequest(identifier, request.getfixturevalue(file_fixture), ValidationMode.METADATA, metadata)
            )

        without = validate_with(None)
        empty = validate_with(EOMetadata())
        assert without.status == empty.status
        assert [e.message for e in without.events] == [e.message for e in empty.events]
        assert any("skipping CRS validation" in e.message for e in without.infos())
