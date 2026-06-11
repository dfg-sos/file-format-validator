"""FileInput fixtures for EO Format Validator tests."""
import pytest
from pathlib import Path

from eo_format_validator.model import FileInput, MultiFileInput

# ========== Data Directory ==========
DATA_DIR = Path("data/geo")


# ========== Raster File Input Fixtures ==========

@pytest.fixture
def geotiff_input():
    """FileInput for GeoTIFF file."""
    return FileInput(path=DATA_DIR / "WSF2019_v1_8_48.tif")


@pytest.fixture
def cog_input():
    """FileInput for Cloud Optimized GeoTIFF file."""
    return FileInput(path=DATA_DIR / "WSF2019_v1_8_48.tif")


@pytest.fixture
def dem_input():
    """FileInput for DEM file."""
    return FileInput(path=DATA_DIR / "WSF2019_v1_8_48.tif")


@pytest.fixture
def dsm_input():
    """FileInput for DSM file."""
    return FileInput(path=DATA_DIR / "WSF2019_v1_8_48.tif")


@pytest.fixture
def dtm_input():
    """FileInput for DTM file."""
    return FileInput(path=DATA_DIR / "WSF2019_v1_8_48.tif")


@pytest.fixture
def grib_input():
    """FileInput for GRIB file."""
    return FileInput(path=DATA_DIR / "grib_beispiel.grb")


@pytest.fixture
def netcdf_input():
    """FileInput for NetCDF file."""
    return FileInput(path=DATA_DIR / "pr_2018.nc")


# ========== Vector File Input Fixtures ==========

@pytest.fixture
def geojson_input():
    """FileInput for GeoJSON file."""
    return FileInput(path=DATA_DIR / "geojson_de.json")


@pytest.fixture
def geopackage_input():
    """FileInput for GeoPackage file (vector)."""
    return FileInput(path=DATA_DIR / "Italian_cities.gpkg")


@pytest.fixture
def geoparquet_input():
    """FileInput for GeoParquet file."""
    return FileInput(path=DATA_DIR / "hannover_buildings.geoparquet")


@pytest.fixture
def gml_input():
    """FileInput for GML file."""
    return FileInput(path=DATA_DIR / "GK1000_GeologicStructure.gml")


@pytest.fixture
def gpx_input():
    """FileInput for GPX file."""
    return FileInput(path=DATA_DIR / "Sauschwaenzleweg.gpx")


@pytest.fixture
def kml_input():
    """FileInput for KML file."""
    return FileInput(path=DATA_DIR / "KML_Samples.kml")


@pytest.fixture
def wkt_input():
    """FileInput for WKT file."""
    return FileInput(path=DATA_DIR / "test_geometries_epsg4326.wkt")


# ========== MultiFileInput Fixtures ==========

@pytest.fixture
def shapefile_input():
    """MultiFileInput for Shapefile with all auxiliary files."""
    shp_file = DATA_DIR / "Shapefile1" / "gis_osm_buildings_a_free_1.shp"
    shx_file = DATA_DIR / "Shapefile1" / "gis_osm_buildings_a_free_1.shx"
    dbf_file = DATA_DIR / "Shapefile1" / "gis_osm_buildings_a_free_1.dbf"
    prj_file = DATA_DIR / "Shapefile1" / "gis_osm_buildings_a_free_1.prj"
    cpg_file = DATA_DIR / "Shapefile1" / "gis_osm_buildings_a_free_1.cpg"
    return MultiFileInput(
        path=shp_file,
        secondary_files={shx_file, dbf_file, prj_file, cpg_file}
    )


# ========== Additional File Input Fixtures ==========

@pytest.fixture
def geopackage_raster_input():
    """FileInput for raster-only GeoPackage file."""
    return FileInput(path=DATA_DIR / "test_raster_only_full.gpkg")


@pytest.fixture
def geopackage_vector_input():
    """FileInput for vector GeoPackage file (StLouis)."""
    return FileInput(path=DATA_DIR / "StLouis.gpkg")


@pytest.fixture
def fells_loop_gpx_input():
    """FileInput for GPX v1.0 file."""
    return FileInput(path=DATA_DIR / "fells_loop.gpx")


@pytest.fixture
def wkt_sparql_input():
    """FileInput for GeoSPARQL WKT file."""
    return FileInput(path=DATA_DIR / "wkt_example.wkt")


@pytest.fixture
def example_parquet_input():
    """FileInput for plain Parquet file (may not have geo metadata)."""
    return FileInput(path=DATA_DIR / "example.parquet")


@pytest.fixture
def copied_tif_input():
    """FileInput for copied TIFF file."""
    return FileInput(path=DATA_DIR / "copied.tif")


@pytest.fixture
def o41078a2_tif_input():
    """FileInput for o41078a2.tif file."""
    return FileInput(path=DATA_DIR / "o41078a2.tif")


@pytest.fixture
def cyprus_grib_input():
    """FileInput for Cyprus SKIRON GRIB file."""
    return FileInput(path=DATA_DIR / "Cyprus_SKIRON_090326.grb")


@pytest.fixture
def sresa1b_netcdf_input():
    """FileInput for sresa1b_ncar_ccsm3-example.nc file."""
    return FileInput(path=DATA_DIR / "sresa1b_ncar_ccsm3-example.nc")


# ========== Negative Test Fixtures ==========

@pytest.fixture
def nonexistent_input():
    """FileInput for non-existent file (generic)."""
    return FileInput(path=Path("/nonexistent/file.xyz"))