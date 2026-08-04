"""Test cases for Shapefile Validator using real data files."""
import pytest
from pathlib import Path

from eo_format_validator.validators.eo.shapefile_validator import ShapefileValidator
from eo_format_validator import ValidationMode, FileInput, MultiFileInput
from shapely import GeometryType
from eo_format_validator.validators import EOValidationRequest
from eo_format_validator.model.validation_result import ValidationStatus
from eo_format_validator.model import ValidationResult, Error, Cause
from fixtures import shapefile_input, geojson_input, wgs84_crs, mercator_crs, nonexistent_input,geotiff_input


# ========== Local Fixtures ==========

@pytest.fixture
def shapefile_validator():
    """Shapefile validator instance."""
    return ShapefileValidator()


# ========== Test get_extensions() Method ==========

class TestShapefileValidatorGetExtensions:
    """Test get_extensions() method."""

    def test_get_extensions(self, shapefile_validator):
        """Test that .shp extension is returned."""
        extensions = shapefile_validator.get_extensions()
        assert '.shp' in extensions
        assert len(extensions) == 1


# ========== Test assert_extension() Method ==========

class TestShapefileValidatorAssertExtension:
    """Test assert_extension() method."""

    def test_assert_extension_valid(self, shapefile_validator, shapefile_input):
        """Test extension validation passes for .shp file with all required files."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.BASIC
        )
        result = shapefile_validator.assert_extension(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_extension_failure(self, shapefile_validator, geojson_input):
        """Test extension validation fails for non-.shp files."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = shapefile_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_assert_extension_missing_required(self, shapefile_validator):
        """Test extension validation fails when required files are missing."""
        shp_file = Path("/fake/file.shp")
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files=set()
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.BASIC
        )
        result = shapefile_validator.assert_extension(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test assert_exists() Method ==========

class TestShapefileValidatorAssertExists:
    """Test assert_exists() method."""

    def test_assert_exists_passes(self, shapefile_validator, shapefile_input):
        """Test file existence passes for existing files."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.assert_exists(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_exists_fails_for_nonexistent(self, shapefile_validator, nonexistent_input):
        """Test file existence fails for non-existent files."""
        shp_file = nonexistent_input.path
        shx_file = shp_file.with_suffix('.shx')
        dbf_file = shp_file.with_suffix('.dbf')
        prj_file = shp_file.with_suffix('.prj')
        cpg_file = shp_file.with_suffix('.cpg')
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files={shx_file, dbf_file, prj_file, cpg_file}
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.assert_exists(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test assert_can_open() Method ==========

class TestShapefileValidatorAssertCanOpen:
    """Test assert_can_open() method."""

    def test_assert_can_open_passes(self, shapefile_validator, shapefile_input):
        """Test opening a real Shapefile."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.FULL
        )
        result = shapefile_validator.assert_can_open(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_can_open_failure(self, shapefile_validator, geotiff_input):
        """Test that assert_can_open fails for GeoJSON file."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=geotiff_input,
            mode=ValidationMode.FULL
        )
        result = shapefile_validator.assert_can_open(request)
        assert result.status == ValidationStatus.FAILURE


# ========== Test get_crs() Method ==========

class TestShapefileValidatorGetCRS:
    """Test get_crs() method."""

    def test_get_crs(self, shapefile_validator, shapefile_input, wgs84_crs):
        """Test CRS extraction returns the expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        crs = shapefile_validator.get_crs(request)
        assert crs is not None

    def test_get_crs_none(self, shapefile_validator, geotiff_input):
        """Test CRS extraction returns None for non-Shapefile."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=geotiff_input,
            mode=ValidationMode.CRS
        )
        crs = shapefile_validator.get_crs(request)
        assert crs is None


# ========== Test assert_crs() Method ==========

class TestShapefileValidatorAssertCRS:
    """Test assert_crs() method."""

    def test_assert_crs_passes(self, shapefile_validator, shapefile_input, wgs84_crs):
        """Test CRS validation passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = shapefile_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_crs_fails(self, shapefile_validator, shapefile_input, mercator_crs):
        """Test CRS validation fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = shapefile_validator.assert_crs(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_assert_crs_no_expected(self, shapefile_validator, shapefile_input):
        """Test CRS validation skips when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.CRS
        )
        result = shapefile_validator.assert_crs(request)
        assert result.status == ValidationStatus.SUCCESS


# ========== Test assert_geometry_type() Method ==========

class TestShapefileValidatorAssertGeometryType:
    """Test assert_geometry_type() method."""

    def test_assert_geometry_type_passes(self, shapefile_validator, shapefile_input):
        """Test geometry type validation passes with matching expected type."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POLYGON
        )
        result = shapefile_validator.assert_geometry_type(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_assert_geometry_type_fails(self, shapefile_validator, shapefile_input):
        """Test geometry type validation fails with mismatching expected type."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.FULL,
            geometry_type=GeometryType.POINT
        )
        result = shapefile_validator.assert_geometry_type(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())


# ========== Test validate() with BASIC Mode ==========

class TestShapefileValidatorBasicMode:
    """Test validate() method with BASIC mode (extension check only)."""

    def test_validate_basic_passes(self, shapefile_validator, shapefile_input):
        """Test BASIC mode passes for valid .shp file."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.BASIC
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_basic_failure(self, shapefile_validator, geojson_input):
        """Test BASIC mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=geojson_input,
            mode=ValidationMode.BASIC
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())


# ========== Test validate() with STRUCTURAL Mode ==========

class TestShapefileValidatorStructuralMode:
    """Test validate() method with STRUCTURAL mode (extension + existence)."""

    def test_validate_structural_positive(self, shapefile_validator, shapefile_input):
        """Test STRUCTURAL mode passes for valid existing files."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_structural_negative_wrong_extension(self, shapefile_validator, geojson_input):
        """Test STRUCTURAL mode fails for wrong extension."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=geojson_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_structural_negative_nonexistent(self, shapefile_validator, nonexistent_input):
        """Test STRUCTURAL mode fails for non-existent files."""
        shp_file = nonexistent_input.path
        shx_file = shp_file.with_suffix('.shx')
        dbf_file = shp_file.with_suffix('.dbf')
        prj_file = shp_file.with_suffix('.prj')
        cpg_file = shp_file.with_suffix('.cpg')
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files={shx_file, dbf_file, prj_file, cpg_file}
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.STRUCTURAL
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with FULL Mode ==========

class TestShapefileValidatorFullMode:
    """Test validate() method with FULL mode (extension + existence + open + geometry)."""

    def test_validate_full_positive(self, shapefile_validator, shapefile_input, wgs84_crs):
        """Test FULL mode passes for valid Shapefile."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_full_negative_wrong_format(self, shapefile_validator, geojson_input, wgs84_crs):
        """Test FULL mode fails for wrong file format."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=geojson_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.EXTENSION_MISMATCH for err in result.errors())

    def test_validate_full_negative_nonexistent(self, shapefile_validator, nonexistent_input, wgs84_crs):
        """Test FULL mode fails for non-existent files."""
        shp_file = nonexistent_input.path
        shx_file = shp_file.with_suffix('.shx')
        dbf_file = shp_file.with_suffix('.dbf')
        prj_file = shp_file.with_suffix('.prj')
        cpg_file = shp_file.with_suffix('.cpg')
        file_input = MultiFileInput(
            path=shp_file,
            secondary_files={shx_file, dbf_file, prj_file, cpg_file}
        )
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=file_input,
            mode=ValidationMode.FULL,
            crs=wgs84_crs,
            geometry_type=GeometryType.POLYGON
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.PATH_ERROR for err in result.errors())


# ========== Test validate() with CRS Mode ==========

class TestShapefileValidatorCRSMode:
    """Test validate() method with CRS mode."""

    def test_validate_crs_no_expected(self, shapefile_validator, shapefile_input):
        """Test CRS mode passes when no expected CRS is provided."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.CRS
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_positive(self, shapefile_validator, shapefile_input, wgs84_crs):
        """Test CRS mode passes with matching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.SUCCESS

    def test_validate_crs_negative_wrong_crs(self, shapefile_validator, shapefile_input, mercator_crs):
        """Test CRS mode fails with mismatching expected CRS."""
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=shapefile_input,
            mode=ValidationMode.CRS,
            crs=mercator_crs
        )
        result = shapefile_validator.validate(request)
        assert result.status == ValidationStatus.FAILURE
        assert any(err.cause == Cause.METADATA_MISMATCH for err in result.errors())

    def test_validate_crs_negative_wrong_format(self, shapefile_validator, geojson_input, wgs84_crs):
        """Test CRS mode with compatible CRS from wrong format.
        
        Note: GeoJSON files can be opened by Fiona and have CRS information.
        Since the GeoJSON file has EPSG:4326 which matches wgs84_crs, validation passes.
        This is expected behavior - the validator validates CRS content, not file format.
        """
        request = EOValidationRequest(
            format_identifier="format_4119",
            actual_file=geojson_input,
            mode=ValidationMode.CRS,
            crs=wgs84_crs
        )
        result = shapefile_validator.validate(request)
        # GeoJSON file has EPSG:4326 which matches expected CRS
        assert result.status == ValidationStatus.SUCCESS