"""CRS fixtures for EO Format Validator tests."""
import pytest
from pyproj import CRS


@pytest.fixture
def mercator_crs():
    """A CRS that doesn't match the test file (Web Mercator, EPSG:3857)."""
    return CRS.from_epsg(3857)


@pytest.fixture
def wgs84_crs():
    """WGS 84 CRS (EPSG:4326)."""
    return CRS.from_epsg(4326)


@pytest.fixture
def utm32n_crs():
    """UTM Zone 32N CRS (EPSG:32632)."""
    return CRS.from_epsg(32632)