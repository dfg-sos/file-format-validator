"""Test cases for GML Validator using real data files."""
import pytest
from pathlib import Path
import xml.etree.ElementTree as ET

from eo_format_validator.validators.gml_validator import GMLValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


@pytest.fixture
def gml_validator():
    """Create the actual GML validator instance."""
    return GMLValidator()


@pytest.fixture
def gk1000_gml():
    """Use the real GML file (INSPIRE Geology, GML 3.2)."""
    return DATA_DIR / "GK1000_GeologicStructure.gml"


@pytest.fixture
def validation_request(gk1000_gml):
    """Create a validation request using the real GML file."""
    return EOValidationRequest(
        format_identifier="format_4111",
        actual_file=FileInput(path=gk1000_gml),
        mode=ValidationMode.STRUCTURAL
    )


class TestGMLValidatorExtension:
    """Test GML validator extension handling."""

    def test_get_extensions(self, gml_validator):
        """Test that GML validator accepts gml and xml extensions."""
        extensions = gml_validator.get_extensions()
        assert '.gml' in extensions
        assert '.xml' in extensions
        assert len(extensions) == 2


class TestGMLValidatorAssertExists:
    """Test GML validator file existence checks."""

    def test_assert_exists_passes(self, gml_validator, gk1000_gml):
        """Test file existence passes for the real GML file."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=FileInput(path=gk1000_gml),
            mode=ValidationMode.STRUCTURAL
        )
        result = gml_validator.assert_exists(request)
        assert result.status.value == "success"


class TestGMLValidatorExtractNamespace:
    """Test GML validator namespace extraction."""

    def test_extract_namespace_from_gk1000(self, gml_validator, gk1000_gml):
        """Test namespace extraction from the real GML file."""
        tree = ET.parse(str(gk1000_gml))
        root = tree.getroot()
        namespace = gml_validator._extract_namespace(root)
        assert namespace == "http://www.opengis.net/gml/3.2"

    def test_extract_namespace_no_namespace(self, gml_validator):
        """Test namespace extraction with no namespace."""
        root = ET.fromstring('<root/>')
        namespace = gml_validator._extract_namespace(root)
        assert namespace is None


class TestGMLValidatorFullValidation:
    """Test GML validator full validation workflow."""

    def test_validate_structural_mode(self, gml_validator, validation_request):
        """Test validation in structural mode with real GML file."""
        result = gml_validator.validate(validation_request)
        assert result.status.value == "success"

    def test_validate_full_mode(self, gml_validator, gk1000_gml):
        """Test validation in full mode (opens via fiona)."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=FileInput(path=gk1000_gml),
            mode=ValidationMode.FULL
        )
        result = gml_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_basic_mode(self, gml_validator, gk1000_gml):
        """Test validation in basic mode."""
        request = EOValidationRequest(
            format_identifier="format_4111",
            actual_file=FileInput(path=gk1000_gml),
            mode=ValidationMode.BASIC
        )
        result = gml_validator.validate(request)
        assert result.status.value == "success"