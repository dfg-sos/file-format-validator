"""Tests for parsing expected metadata from plain strings via the format's validator."""
import pytest
from pyproj import CRS
from shapely import GeometryType

from format_validator import (
    FormatValidator,
    FormatIdentifier,
    ValidationRequest,
    ValidationMode,
    ValidationStatus,
    Cause,
    EOMetadata,
    UnsupportedMetadataKeys,
    InvalidMetadataValue,
)
from test.fixtures import geojson_input, geotiff_input, wgs84_crs


UNREGISTERED = FormatIdentifier("test_unregistered_metadata")


class TestSupportedMetadataKeys:
    @pytest.mark.parametrize(
        "identifier",
        [FormatIdentifier.GEOJSON, FormatIdentifier.SHAPEFILE, FormatIdentifier.GEOPACKAGE],
    )
    def test_vector_formats(self, identifier):
        assert FormatValidator.supported_metadata_keys(identifier) == {"crs", "geometry_type"}

    @pytest.mark.parametrize("identifier", [FormatIdentifier.GEOTIFF, FormatIdentifier.COG])
    def test_raster_formats(self, identifier):
        assert FormatValidator.supported_metadata_keys(identifier) == {"crs"}

    def test_unregistered_format(self):
        assert FormatValidator.supported_metadata_keys(UNREGISTERED) == frozenset()


class TestParseMetadata:
    def test_valid_values(self):
        metadata = FormatValidator.parse_metadata(
            FormatIdentifier.GEOJSON, {"crs": "EPSG:4326", "geometry_type": "Polygon"}
        )
        assert metadata == EOMetadata(crs=CRS.from_epsg(4326), geometry_type=GeometryType.POLYGON)

    def test_raster_crs(self):
        metadata = FormatValidator.parse_metadata(FormatIdentifier.GEOTIFF, {"crs": "EPSG:4326"})
        assert metadata == EOMetadata(crs=CRS.from_epsg(4326))

    @pytest.mark.parametrize("values", [{}, {"crs": "", "geometry_type": ""}])
    def test_no_values_gives_empty_metadata(self, values):
        assert FormatValidator.parse_metadata(FormatIdentifier.GEOJSON, values) == EOMetadata()

    def test_empty_value_for_unsupported_key_is_ignored(self):
        assert FormatValidator.parse_metadata(FormatIdentifier.GEOTIFF, {"geometry_type": ""}) == EOMetadata()

    def test_unregistered_format_without_values(self):
        assert FormatValidator.parse_metadata(UNREGISTERED, {}) is None


class TestParseMetadataErrors:
    def test_unknown_key(self):
        with pytest.raises(UnsupportedMetadataKeys) as exc_info:
            FormatValidator.parse_metadata(FormatIdentifier.GEOJSON, {"crs": "EPSG:4326", "foo": "bar"})
        assert exc_info.value.unknown == {"foo"}
        assert exc_info.value.supported == {"crs", "geometry_type"}

    def test_geometry_type_for_raster(self):
        with pytest.raises(UnsupportedMetadataKeys) as exc_info:
            FormatValidator.parse_metadata(FormatIdentifier.GEOTIFF, {"geometry_type": "Polygon"})
        assert exc_info.value.unknown == {"geometry_type"}
        assert exc_info.value.supported == {"crs"}

    def test_unknown_key_for_unregistered_format(self):
        with pytest.raises(UnsupportedMetadataKeys) as exc_info:
            FormatValidator.parse_metadata(UNREGISTERED, {"crs": "EPSG:4326"})
        assert exc_info.value.unknown == {"crs"}
        assert exc_info.value.supported == frozenset()

    @pytest.mark.parametrize(
        "values", [{"crs": "not-a-crs"}, {"geometry_type": "NotAGeometry"}], ids=["crs", "geometry_type"]
    )
    def test_invalid_value(self, values):
        with pytest.raises(InvalidMetadataValue) as exc_info:
            FormatValidator.parse_metadata(FormatIdentifier.GEOJSON, values)
        assert exc_info.value.__cause__ is not None


class TestParsedMetadataValidation:
    def test_full_mode_matches_hand_built_metadata(self, geojson_input, wgs84_crs):
        def validate(metadata):
            return FormatValidator.validate(
                ValidationRequest(
                    format_identifier=FormatIdentifier.GEOJSON,
                    actual_file=geojson_input,
                    mode=ValidationMode.FULL,
                    metadata=metadata,
                )
            )

        parsed = FormatValidator.parse_metadata(FormatIdentifier.GEOJSON, {"crs": "EPSG:4326"})
        expected = validate(EOMetadata(crs=wgs84_crs))
        actual = validate(parsed)
        assert actual.status == expected.status
        assert [e.message for e in actual.events] == [e.message for e in expected.events]


class TestUnsupportedMetadataType:
    @pytest.mark.parametrize("mode", list(ValidationMode))
    @pytest.mark.parametrize(
        "identifier, file_fixture",
        [(FormatIdentifier.GEOJSON, "geojson_input"), (FormatIdentifier.GEOTIFF, "geotiff_input")],
        ids=["vector", "raster"],
    )
    def test_raw_mapping_fails(self, identifier, file_fixture, mode, request):
        result = FormatValidator.validate(
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
        result = FormatValidator.validate(
            ValidationRequest(format_identifier=FormatIdentifier.GEOJSON, actual_file=geojson_input, mode=mode)
        )
        assert result.status == ValidationStatus.SUCCESS
