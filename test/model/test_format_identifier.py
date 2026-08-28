"""Tests for the FormatIdentifier value object."""
import pytest
from format_validator.model.format_identifier import FormatIdentifier


class TestStringRepr:
    def test_str(self):
        assert str(FormatIdentifier.GEOTIFF) == "GeoTIFF"

    def test_repr(self):
        assert "FormatIdentifier" in repr(FormatIdentifier.GEOTIFF)
        assert "GeoTIFF" in repr(FormatIdentifier.GEOTIFF)


class TestEqualityHash:
    def test_equality(self):
        a = FormatIdentifier.GEOTIFF
        b = FormatIdentifier.GEOTIFF
        c = FormatIdentifier.COG
        assert a == b
        assert a != c
        assert a != "GeoTIFF"

    def test_hash(self):
        a = FormatIdentifier.GEOTIFF
        b = FormatIdentifier.GEOTIFF
        assert hash(a) == hash(b)
        d = {a: "found"}
        assert d[b] == "found"


class TestSingleton:
    def test_same_instance(self):
        a = FormatIdentifier.GEOTIFF
        b = FormatIdentifier("GeoTIFF")
        assert a is b

    def test_new_format_registered(self):
        custom = FormatIdentifier("CustomFormat", description="A custom format", is_abstract=False)
        assert FormatIdentifier.get("CustomFormat") is custom
        assert custom in FormatIdentifier.all()

    def test_reuse_existing(self):
        first = FormatIdentifier("ReuseMe")
        second = FormatIdentifier("ReuseMe", description="ignored")
        assert first is second
        assert second.description == ""  # first definition wins


class TestTaxonomy:
    def test_abstract_format_has_children(self):
        raster = FormatIdentifier.RASTER
        assert raster.is_abstract
        assert len(raster.children) > 0
        assert FormatIdentifier.GEOTIFF in raster.children

    def test_concrete_format_no_children(self):
        gml = FormatIdentifier.GML
        assert not gml.is_abstract
        assert gml.children == []

    def test_geotiff_is_not_abstract_despite_children(self):
        geotiff = FormatIdentifier.GEOTIFF
        assert not geotiff.is_abstract
        assert len(geotiff.children) > 0
        assert FormatIdentifier.COG in geotiff.children
    def test_parent(self):
        assert FormatIdentifier.GEOTIFF.parent == FormatIdentifier.RASTER
        assert FormatIdentifier.COG.parent == FormatIdentifier.GEOTIFF
        assert FormatIdentifier.RASTER.parent == FormatIdentifier.GIS
        assert FormatIdentifier.GIS.parent is None

    def test_leaves(self):
        raster = FormatIdentifier.RASTER
        leaves = raster.leaves
        assert FormatIdentifier.COG in leaves
        assert FormatIdentifier.GEOTIFF in leaves # GEOTIFF is a leaf because it is not abstract
        assert FormatIdentifier.SHAPEFILE not in leaves

    def test_vector_leaves(self):
        vector = FormatIdentifier.VECTOR
        leaves = vector.leaves
        assert FormatIdentifier.SHAPEFILE in leaves
        assert FormatIdentifier.GEOJSON in leaves
        assert FormatIdentifier.GEOPARQUET in leaves

    def test_gis_data_leaves(self):
        gis = FormatIdentifier.GIS
        leaves = gis.leaves
        assert FormatIdentifier.COG in leaves
        assert FormatIdentifier.SHAPEFILE in leaves
        assert FormatIdentifier.GEOTIFF in leaves

    def test_all_returns_sorted(self):
        all_formats = FormatIdentifier.all()
        labels = [f.value for f in all_formats]
        assert labels == sorted(labels)
        assert FormatIdentifier.GEOTIFF in all_formats
