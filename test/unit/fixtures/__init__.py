"""Fixtures for EO Format Validator tests.

This package provides reusable pytest fixtures organized by category:
- file_inputs: FileInput and MultiFileInput fixtures for test data files
- crs_fixtures: CRS-related fixtures for CRS testing
- validation_requests: Parametrized validation request fixtures
"""

from .file_inputs import *
from .crs_fixtures import *
from .validation_requests import *

__all__ = [
    # File inputs - raster
    "geotiff_input",
    "cog_input",
    "dem_input",
    "dsm_input",
    "dtm_input",
    "grib_input",
    "netcdf_input",
    # File inputs - vector
    "geojson_input",
    "geopackage_input",
    "geoparquet_input",
    "gml_input",
    "gpx_input",
    "kml_input",
    "wkt_input",
    # File inputs - multi-file
    "shapefile_input",
    # File inputs - additional
    "geopackage_raster_input",
    "geopackage_vector_input",
    "fells_loop_gpx_input",
    "wkt_sparql_input",
    "example_parquet_input",
    "copied_tif_input",
    "o41078a2_tif_input",
    "cyprus_grib_input",
    "sresa1b_netcdf_input",
    # File inputs - negative tests
    "nonexistent_input",
    # CRS fixtures
    "mercator_crs",
    "wgs84_crs",
    "utm32n_crs",
    # Validation request fixtures
    "validator_file_pair",
    "validation_mode",
    "validation_request_with_mode",
]