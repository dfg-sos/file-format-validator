"""Test cases for WKT Validator using real data files."""
import pytest
from pathlib import Path
from shapely import GeometryType

from eo_format_validator.validators.wkt_validator import WKTValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


@pytest.fixture
def wkt_validator():
    """Create the actual WKT validator instance."""
    return WKTValidator()


@pytest.fixture
def test_geometries_wkt():
    """Use the real test_geometries_epsg4326.wkt file (EWKT format)."""
    return DATA_DIR / "test_geometries_epsg4326.wkt"


@pytest.fixture
def wkt_example_file():
    """Use the real wkt_example.wkt file (GeoSPARQL format)."""
    return DATA_DIR / "wkt_example.wkt"


class TestWKTValidatorExtension:
    """Test WKT validator extension handling."""

    def test_get_extensions(self, wkt_validator):
        """Test that WKT validator accepts expected extensions."""
        extensions = wkt_validator.get_extensions()
        assert '.wkt' in extensions
        assert '.txt' in extensions
        assert len(extensions) == 2


class TestWKTValidatorAssertCanOpen:
    """Test WKT validator open/assertion functionality."""

    def test_assert_can_open_with_ewkt(self, wkt_validator, test_geometries_wkt):
        """Test successful validation of a real EWKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=test_geometries_wkt),
            mode=ValidationMode.FULL
        )
        result = wkt_validator.assert_can_open(request)
        assert result.status.value == "success"

    def test_assert_can_open_with_sparql_wkt(self, wkt_validator, wkt_example_file):
        """Test successful validation of a real GeoSPARQL WKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=wkt_example_file),
            mode=ValidationMode.FULL
        )
        result = wkt_validator.assert_can_open(request)
        assert result.status.value == "success"


class TestWKTValidatorCRS:
    """Test WKT validator CRS functionality."""

    def test_get_crs_from_ewkt(self, wkt_validator, test_geometries_wkt):
        """Test CRS extraction from EWKT file (SRID=4326)."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=test_geometries_wkt),
            mode=ValidationMode.CRS
        )
        crs = wkt_validator.get_crs(request)
        assert crs is not None
        assert crs.to_epsg() == 4326

    def test_get_crs_from_sparql_wkt(self, wkt_validator, wkt_example_file):
        """Test CRS extraction from GeoSPARQL WKT file (EPSG:31370)."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=wkt_example_file),
            mode=ValidationMode.CRS
        )
        crs = wkt_validator.get_crs(request)
        assert crs is not None
        assert crs.to_epsg() == 31370


class TestWKTValidatorGeometryType:
    """Test WKT validator geometry type functionality."""

    def test_assert_geometry_type_point_from_ewkt(self, wkt_validator, test_geometries_wkt):
        """Test detecting POINT geometry from EWKT file (first geometry)."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=test_geometries_wkt),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        result = wkt_validator.assert_geometry_type(request)
        assert result.status.value == "success"

    def test_assert_geometry_type_geometrycollection_from_sparql(self, wkt_validator, wkt_example_file):
        """Test detecting GEOMETRYCOLLECTION from GeoSPARQL WKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=wkt_example_file),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.GEOMETRYCOLLECTION
        )
        result = wkt_validator.assert_geometry_type(request)
        assert result.status.value == "success"


class TestWKTValidatorFullValidation:
    """Test WKT validator full validation workflow."""

    def test_validate_structural_with_ewkt(self, wkt_validator, test_geometries_wkt):
        """Test structural validation with a real EWKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=test_geometries_wkt),
            mode=ValidationMode.STRUCTURAL
        )
        result = wkt_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full_with_ewkt(self, wkt_validator, test_geometries_wkt):
        """Test full validation with a real EWKT file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=test_geometries_wkt),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        result = wkt_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full_with_sparql_wkt(self, wkt_validator, wkt_example_file):
        """Test full validation with the GeoSPARQL WKT example file."""
        request = EOValidationRequest(
            format_identifier="format_4122",
            actual_file=FileInput(path=wkt_example_file),
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.GEOMETRYCOLLECTION
        )
        result = wkt_validator.validate(request)
        assert result.status.value == "success"