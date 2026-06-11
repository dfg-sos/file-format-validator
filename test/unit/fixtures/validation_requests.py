"""Parametrized validation request fixtures for EO Format Validator tests."""
import pytest

from eo_format_validator.model import ValidationMode
from eo_format_validator.validators import EOValidationRequest


@pytest.fixture(
    params=[
        # (format_identifier, file_input_fixture_name, validator_fixture_name)
        ("format_4100", "cog_input", "cog_validator"),
        ("format_4109", "geotiff_input", "geotiff_validator"),
        ("format_4102", "dem_input", "dem_validator"),
        ("format_4103", "dsm_input", "dsm_validator"),
        ("format_4104", "dtm_input", "dtm_validator"),
        ("format_4113", "grib_input", "grib_validator"),
        ("format_4115", "netcdf_input", "netcdf_validator"),
        ("format_4106", "geojson_input", "geojson_validator"),
        ("format_4107", "geopackage_input", "geopackage_validator"),
        ("format_4108", "geoparquet_input", "geoparquet_validator"),
        ("format_4119", "shapefile_input", "shapefile_validator"),
        ("format_4111", "gml_input", "gml_validator"),
        ("format_4112", "gpx_input", "gpx_validator"),
        ("format_4114", "kml_input", "kml_validator"),
        ("format_4122", "wkt_input", "wkt_validator"),
    ],
    ids=[
        "format_4100_cog",
        "format_4109_geotiff",
        "format_4102_dem",
        "format_4103_dsm",
        "format_4104_dtm",
        "format_4113_grib",
        "format_4115_netcdf",
        "format_4106_geojson",
        "format_4107_geopackage",
        "format_4108_geoparquet",
        "format_4119_shapefile",
        "format_4111_gml",
        "format_4112_gpx",
        "format_4114_kml",
        "format_4122_wkt",
    ]
)
def validator_file_pair(request):
    """
    Parametrized fixture returning (format_identifier, file_input, validator) tuples.
    
    Requires validator fixtures to be available (define them in your test file or conftest.py).
    """
    format_id, input_fixture_name, validator_fixture_name = request.param
    file_input = request.getfixturevalue(input_fixture_name)
    validator = request.getfixturevalue(validator_fixture_name)
    return format_id, file_input, validator


@pytest.fixture(
    params=[ValidationMode.BASIC, ValidationMode.STRUCTURAL, ValidationMode.FULL, ValidationMode.CRS],
    ids=["basic", "structural", "full", "crs"]
)
def validation_mode(request):
    """Parametrized fixture for ValidationMode."""
    return request.param


@pytest.fixture
def validation_request_with_mode(validator_file_pair, validation_mode):
    """
    Parametrized fixture returning EOValidationRequest for all validator/file pairs
    with all validation modes.
    
    Usage:
        def test_something(validation_request_with_mode):
            format_id, file_input, validator, mode, request = validation_request_with_mode
            result = validator.validate(request)
    """
    format_id, file_input, validator = validator_file_pair
    mode = validation_mode
    request = EOValidationRequest(
        format_identifier=format_id,
        actual_file=file_input,
        mode=mode
    )
    return (format_id, file_input, validator, mode, request)