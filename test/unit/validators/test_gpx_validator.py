"""Test cases for GPX Validator using real data files."""
import pytest
from pathlib import Path
import xml.etree.ElementTree as ET

from eo_format_validator.validators.gpx_validator import GPXValidator
from eo_format_validator.model import ValidationRequest, ValidationResult, ValidationMode, FileInput, Cause
from eo_format_validator.validators.eo_file_format_validator import EOValidationRequest

DATA_DIR = Path("data/geo")


@pytest.fixture
def gpx_validator():
    """Create the actual GPX validator instance."""
    return GPXValidator()


@pytest.fixture
def sauschwaenzleweg_gpx():
    """Use the real GPX v1.1 file."""
    return DATA_DIR / "Sauschwaenzleweg.gpx"


@pytest.fixture
def fells_loop_gpx():
    """Use the real GPX v1.0 file."""
    return DATA_DIR / "fells_loop.gpx"


@pytest.fixture
def validation_request(sauschwaenzleweg_gpx):
    """Create a validation request for STRUCTURAL mode."""
    return EOValidationRequest(
        format_identifier="format_4112",
        actual_file=FileInput(path=sauschwaenzleweg_gpx),
        mode=ValidationMode.STRUCTURAL
    )


class TestGPXValidatorExtension:
    """Test GPX validator extension handling."""

    def test_get_extensions(self, gpx_validator):
        """Test that GPX validator accepts .gpx extension."""
        extensions = gpx_validator.get_extensions()
        assert '.gpx' in extensions
        assert len(extensions) == 1


class TestGPXValidatorAssertExists:
    """Test GPX validator file existence checks."""

    def test_assert_exists_passes(self, gpx_validator, sauschwaenzleweg_gpx):
        """Test file existence passes for real GPX files."""
        request = EOValidationRequest(
            format_identifier="format_4112",
            actual_file=FileInput(path=sauschwaenzleweg_gpx),
            mode=ValidationMode.STRUCTURAL
        )
        result = gpx_validator.assert_exists(request)
        assert result.status.value == "success"

    def test_assert_exists_fails(self, gpx_validator):
        """Test file existence fails for non-existent files."""
        request = EOValidationRequest(
            format_identifier="format_4112",
            actual_file=FileInput(path=Path("/nonexistent/file.gpx")),
            mode=ValidationMode.STRUCTURAL
        )
        result = gpx_validator.assert_exists(request)
        assert result.status.value == "failure"


class TestGPXValidatorIsGPXDocument:
    """Test GPX validator document identification using real files."""

    def test_is_gpx_document_with_v11(self, gpx_validator, sauschwaenzleweg_gpx):
        """Test that the real GPX v1.1 file is identified as GPX."""
        root = ET.parse(str(sauschwaenzleweg_gpx)).getroot()
        is_gpx, details = gpx_validator._is_gpx_document(root)
        assert is_gpx is True
        assert details['root_element'] == 'gpx'
        assert 'http://www.topografix.com/GPX/1/1' in details['namespace']

    def test_is_gpx_document_with_v10(self, gpx_validator, fells_loop_gpx):
        """Test that the real GPX v1.0 file is identified as GPX."""
        root = ET.parse(str(fells_loop_gpx)).getroot()
        is_gpx, details = gpx_validator._is_gpx_document(root)
        assert is_gpx is True
        assert details['root_element'] == 'gpx'
        assert 'http://www.topografix.com/GPX/1/0' in details['namespace']

    def test_is_gpx_document_fails_with_wrong_root(self, gpx_validator):
        """Test that non-GPX files are not identified as GPX."""
        root = ET.fromstring('<html><body>test</body></html>')
        is_gpx, details = gpx_validator._is_gpx_document(root)
        assert is_gpx is False

    def test_is_gpx_document_fails_with_wrong_namespace(self, gpx_validator):
        """Test that wrong namespace is not identified as GPX."""
        root = ET.fromstring('<gpx xmlns="http://wrong.namespace.com" />')
        is_gpx, details = gpx_validator._is_gpx_document(root)
        assert is_gpx is False


class TestGPXValidatorFullValidation:
    """Test GPX validator full validation workflow."""

    def test_validate_structural_with_v11(self, gpx_validator, validation_request):
        """Test structural validation with a real GPX v1.1 file."""
        result = gpx_validator.validate(validation_request)
        assert result.status.value == "success"

    def test_validate_structural_with_v10(self, gpx_validator, fells_loop_gpx):
        """Test structural validation with a real GPX v1.0 file."""
        request = EOValidationRequest(
            format_identifier="format_4112",
            actual_file=FileInput(path=fells_loop_gpx),
            mode=ValidationMode.STRUCTURAL
        )
        result = gpx_validator.validate(request)
        assert result.status.value == "success"

    def test_validate_full_with_v11(self, gpx_validator, sauschwaenzleweg_gpx):
        """Test full validation with a real GPX v1.1 file (opens via fiona)."""
        request = EOValidationRequest(
            format_identifier="format_4112",
            actual_file=FileInput(path=sauschwaenzleweg_gpx),
            mode=ValidationMode.FULL
        )
        result = gpx_validator.validate(request)
        assert result.status.value == "success"