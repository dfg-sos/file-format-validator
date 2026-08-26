"""Parametrized validation request fixtures for EO Format Validator tests."""
import pytest

from eo_format_validator.model import ValidationMode, FormatIdentifier
from eo_format_validator.validators import EOValidationRequest


@pytest.fixture(
    params=[
        # (format_identifier, file_input_fixture_name, validator_fixture_name)
        (FormatIdentifier("cog"), "cog_input", "cog_validator"),
        (FormatIdentifier("geotiff"), "geotiff_input", "geotiff_validator"),
        (FormatIdentifier("dem"), "dem_input", "dem_validator"),
        (FormatIdentifier("dsm"), "dsm_input", "dsm_validator"),
        (FormatIdentifier("dtm"), "dtm_input", "dtm_validator"),
        (FormatIdentifier("grib"), "grib_input", "grib_validator"),
        (FormatIdentifier("netcdf"), "netcdf_input", "netcdf_validator"),
        (FormatIdentifier("geojson"), "geojson_input", "geojson_validator"),
        (FormatIdentifier("geopackage"), "geopackage_input", "geopackage_validator"),
        (FormatIdentifier("geoparquet"), "geoparquet_input", "geoparquet_validator"),
        (FormatIdentifier("shapefile"), "shapefile_input", "shapefile_validator"),
        (FormatIdentifier("gml"), "gml_input", "gml_validator"),
        (FormatIdentifier("gpx"), "gpx_input", "gpx_validator"),
        (FormatIdentifier("kml"), "kml_input", "kml_validator"),
        (FormatIdentifier("wkt"), "wkt_input", "wkt_validator"),
    ],
    ids=[
        "cog",
        "geotiff",
        "dem",
        "dsm",
        "dtm",
        "grib",
        "netcdf",
        "geojson",
        "geopackage",
        "geoparquet",
        "shapefile",
        "gml",
        "gpx",
        "kml",
        "wkt",
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