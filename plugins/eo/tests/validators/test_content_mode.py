"""CONTENT mode: faults in the pixels or features that METADATA mode does not read."""
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point

from format_validator import FileInput, FormatIdentifier, ValidationMode, ValidationRequest, ValidationStatus, Cause
from format_validator_eo import EOMetadata
from format_validator_eo.geojson_validator import GeoJSONValidator
from format_validator_eo.geopackage_validator import GeoPackageValidator
from format_validator_eo.geotiff_validator import GeoTIFFValidator
from format_validator_eo.vector_file_validator import MAX_FEATURES_TO_INSPECT
from tests.fixtures import shapefile_input, kml_input
from format_validator_eo import formats


def _request(format_identifier, path, mode, **metadata):
    return ValidationRequest(
        format_identifier=format_identifier,
        actual_file=FileInput(path=path),
        mode=mode,
        metadata=EOMetadata.from_strings(**metadata),
    )


def _write_geotiff(path):
    data = np.random.default_rng(0).integers(0, 255, size=(512, 512), dtype=np.uint8)
    with rasterio.open(path, "w", driver="GTiff", width=512, height=512, count=1, dtype="uint8",
                       crs="EPSG:4326", transform=from_origin(0, 0, 0.001, 0.001)) as dst:
        dst.write(data, 1)


def _lines_then_point(n_lines):
    """LineStrings beyond the sampled features, then one Point."""
    return [LineString([(i, 0), (i, 1)]) for i in range(n_lines)] + [Point(0, 0)]


@pytest.fixture
def geotiff(tmp_path):
    path = tmp_path / "valid.tif"
    _write_geotiff(path)
    return path


@pytest.fixture
def truncated_geotiff(tmp_path, geotiff):
    """The header is intact, the pixel data is cut off halfway."""
    path = tmp_path / "truncated.tif"
    data = geotiff.read_bytes()
    path.write_bytes(data[: len(data) // 2])
    return path


class TestRasterContent:

    def test_valid_geotiff_passes(self, geotiff):
        result = GeoTIFFValidator().validate(_request(formats.GEOTIFF, geotiff, ValidationMode.CONTENT, crs="EPSG:4326"))
        assert result.status == ValidationStatus.SUCCESS

    def test_truncated_pixel_data_passes_metadata(self, truncated_geotiff):
        result = GeoTIFFValidator().validate(_request(formats.GEOTIFF, truncated_geotiff, ValidationMode.METADATA, crs="EPSG:4326"))
        assert result.status == ValidationStatus.SUCCESS

    def test_truncated_pixel_data_fails_content(self, truncated_geotiff):
        result = GeoTIFFValidator().validate(_request(formats.GEOTIFF, truncated_geotiff, ValidationMode.CONTENT, crs="EPSG:4326"))
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.STRUCTURAL_MALFORMED for err in result.errors())

    def test_content_not_read_when_metadata_fails(self, tmp_path):
        path = tmp_path / "not_a_tiff.tif"
        path.write_text('{"type": "FeatureCollection", "features": []}')
        validator = GeoTIFFValidator()
        with patch.object(GeoTIFFValidator, "assert_content") as assert_content:
            result = validator.validate(_request(formats.GEOTIFF, path, ValidationMode.CONTENT))
        assert result.status == ValidationStatus.FAILURE
        assert_content.assert_not_called()


class TestVectorContent:

    @pytest.mark.parametrize("validator, format_identifier, name, driver", [
        (GeoPackageValidator(), formats.GEOPACKAGE, "mixed.gpkg", "GPKG"),
        (GeoJSONValidator(), formats.GEOJSON, "mixed.geojson", "GeoJSON"),
    ])
    def test_point_after_sample_passes_metadata_fails_content(self, tmp_path, validator, format_identifier, name, driver):
        path = tmp_path / name
        gpd.GeoDataFrame(geometry=_lines_then_point(MAX_FEATURES_TO_INSPECT), crs="EPSG:4326").to_file(path, driver=driver)

        metadata = validator.validate(_request(format_identifier, path, ValidationMode.METADATA, geometry_type="LineString"))
        assert metadata.status == ValidationStatus.SUCCESS

        content = validator.validate(_request(format_identifier, path, ValidationMode.CONTENT, geometry_type="LineString"))
        assert content.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH and "1 of 51 features" in err.message for err in content.errors())

    def test_only_compatible_geometries_pass_content(self, tmp_path):
        path = tmp_path / "lines.gpkg"
        gpd.GeoDataFrame(geometry=[LineString([(i, 0), (i, 1)]) for i in range(100)], crs="EPSG:4326").to_file(path, driver="GPKG")
        result = GeoPackageValidator().validate(_request(formats.GEOPACKAGE, path, ValidationMode.CONTENT, geometry_type="MultiLineString"))
        assert result.status == ValidationStatus.SUCCESS

    def test_raster_geopackage_reads_pixels(self, tmp_path):
        path = tmp_path / "raster.gpkg"
        with rasterio.open(path, "w", driver="GPKG", width=256, height=256, count=1, dtype="uint8",
                           crs="EPSG:4326", transform=from_origin(0, 0, 0.001, 0.001)) as dst:
            dst.write(np.ones((256, 256), dtype=np.uint8), 1)
        result = GeoPackageValidator().validate(_request(formats.GEOPACKAGE, path, ValidationMode.CONTENT))
        assert result.status == ValidationStatus.SUCCESS


def test_shapefile_content_passes(shapefile_input):
    from format_validator_eo.shapefile_validator import ShapefileValidator
    request = ValidationRequest(format_identifier=formats.SHAPEFILE, actual_file=shapefile_input, mode=ValidationMode.CONTENT)
    assert ShapefileValidator().validate(request).status == ValidationStatus.SUCCESS


def test_format_without_content_reader_is_uncertain(kml_input):
    from format_validator_eo.kml_validator import KMLValidator
    request = ValidationRequest(format_identifier=formats.KML, actual_file=kml_input, mode=ValidationMode.CONTENT)
    result = KMLValidator().validate(request)
    assert result.status == ValidationStatus.UNCERTAIN
    assert any("Content validation is not implemented" in w.message for w in result.warnings())
