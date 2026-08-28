"""Tests for the format identifier translation layer."""

import pytest
from pathlib import Path

from format_validator.translator import FormatTranslator
from format_validator.model import FormatIdentifier


class TestFormatTranslator:
    """Test suite for FormatTranslator."""

    @pytest.fixture
    def translator(self):
        return FormatTranslator(mappings_dir=Path("test/data/mappings"))

    # ------------------------------------------------------------------
    # to_local
    # ------------------------------------------------------------------

    def test_to_local_with_edam_fork_format_id(self, translator):
        """EDAM fork short IDs should map to local IDs."""
        assert translator.to_local("format_4109") == FormatIdentifier.GEOTIFF
        assert translator.to_local("format_4119") == FormatIdentifier.SHAPEFILE
        assert translator.to_local("format_4106") == FormatIdentifier.GEOJSON

    def test_to_local_with_full_uri(self, translator):
        """Full URIs should be stripped and then mapped."""
        assert translator.to_local("http://edamontology.org/format_4109") == FormatIdentifier.GEOTIFF
        assert translator.to_local("http://edamontology.org/format_4119") == FormatIdentifier.SHAPEFILE

    def test_to_local_with_namespace_prefix(self, translator):
        """Namespace prefixes like 'edam:format_4109' should be handled."""
        assert translator.to_local("edam:format_4109") == FormatIdentifier.GEOTIFF

    def test_to_local_unknown_format(self, translator):
        """Unknown format IDs should return None."""
        assert translator.to_local("format_9999") is None
        assert translator.to_local("unknown_format") is None

    def test_to_local_with_ontology_uri(self, translator):
        """When ontology_uri is specified, only that ontology is searched."""
        # The default EDAM fork mapping should work when specified
        assert translator.to_local("format_4109", "http://edamontology.org") == FormatIdentifier.GEOTIFF
        # Unknown ontology should fall through to search all
        assert translator.to_local("format_4109", "http://unknown.org") == FormatIdentifier.GEOTIFF

    # ------------------------------------------------------------------
    # to_external
    # ------------------------------------------------------------------

    def test_to_external(self, translator):
        """Local IDs should reverse-map to external IDs for a given ontology."""
        assert translator.to_external("geotiff", "http://edamontology.org") == "format_4109"
        assert translator.to_external("shapefile", "http://edamontology.org") == "format_4119"

    def test_to_external_unknown_local_id(self, translator):
        """Unknown local IDs should return None."""
        assert translator.to_external("nonexistent", "http://edamontology.org") is None

    def test_to_external_unknown_ontology(self, translator):
        """Unknown ontology should return None and log a warning."""
        assert translator.to_external("geotiff", "http://unknown.org") is None

    # ------------------------------------------------------------------
    # Metadata queries removed – translator is focused on bidirectional 
    # mapping only.  Format-level metadata lives on FormatIdentifier.
    # ------------------------------------------------------------------

    def test_get_loaded_ontologies(self, translator):
        """Should return at least the EDAM ontology."""
        ontologies = translator.get_loaded_ontologies()
        assert "http://edamontology.org" in ontologies
