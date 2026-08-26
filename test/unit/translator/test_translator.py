"""Tests for the format identifier translation layer."""

import pytest
from pathlib import Path

from eo_format_validator.translator import FormatTranslator
from eo_format_validator.model import FormatIdentifier


class TestFormatTranslator:
    """Test suite for FormatTranslator."""

    @pytest.fixture
    def translator(self):
        return FormatTranslator()

    # ------------------------------------------------------------------
    # to_local
    # ------------------------------------------------------------------

    def test_to_local_with_edam_fork_format_id(self, translator):
        """EDAM fork short IDs should map to local IDs."""
        assert translator.to_local("format_4109") == FormatIdentifier("geotiff")
        assert translator.to_local("format_4119") == FormatIdentifier("shapefile")
        assert translator.to_local("format_4106") == FormatIdentifier("geojson")

    def test_to_local_with_full_uri(self, translator):
        """Full URIs should be stripped and then mapped."""
        assert translator.to_local("http://edamontology.org/format_4109") == FormatIdentifier("geotiff")
        assert translator.to_local("http://edamontology.org/format_4119") == FormatIdentifier("shapefile")

    def test_to_local_with_namespace_prefix(self, translator):
        """Namespace prefixes like 'edam:format_4109' should be handled."""
        assert translator.to_local("edam:format_4109") == FormatIdentifier("geotiff")

    def test_to_local_already_local_id(self, translator):
        """Passing an already-local ID should return itself."""
        assert translator.to_local("geotiff") == FormatIdentifier("geotiff")
        assert translator.to_local("shapefile") == FormatIdentifier("shapefile")

    def test_to_local_unknown_format(self, translator):
        """Unknown format IDs should return None."""
        assert translator.to_local("format_9999") is None
        assert translator.to_local("unknown_format") is None

    def test_to_local_with_ontology_uri(self, translator):
        """When ontology_uri is specified, only that ontology is searched."""
        # The default EDAM fork mapping should work when specified
        assert translator.to_local("format_4109", "http://edamontology.org") == FormatIdentifier("geotiff")
        # Unknown ontology should fall through to search all
        assert translator.to_local("format_4109", "http://unknown.org") == FormatIdentifier("geotiff")

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
    # Metadata queries
    # ------------------------------------------------------------------

    def test_get_loaded_ontologies(self, translator):
        """Should return at least the EDAM ontology."""
        ontologies = translator.get_loaded_ontologies()
        assert "http://edamontology.org" in ontologies

    def test_get_local_formats(self, translator):
        """Should return all known local format identifiers."""
        formats = translator.get_local_formats()
        assert FormatIdentifier("geotiff") in formats
        assert FormatIdentifier("shapefile") in formats
        assert FormatIdentifier("geojson") in formats
        assert FormatIdentifier("cog") in formats

    def test_get_local_metadata(self, translator):
        """Should return metadata dict for a known local ID."""
        meta = translator.get_local_metadata("geotiff")
        assert meta is not None
        assert meta["label"] == "GeoTIFF"
        assert meta["category"] == "raster"

    def test_get_local_metadata_unknown(self, translator):
        """Should return None for unknown local IDs."""
        assert translator.get_local_metadata("nonexistent") is None
