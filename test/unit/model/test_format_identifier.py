"""Tests for the FormatIdentifier value object."""
import pytest
from eo_format_validator.model.format_identifier import FormatIdentifier, UnknownFormatError


class TestConstruction:
    def test_from_valid_string(self):
        fi = FormatIdentifier.from_string("geotiff")
        assert fi.value == "geotiff"
        assert fi.label == "GeoTIFF"
        assert fi.category == "raster"

    def test_from_string_alias(self):
        assert FormatIdentifier.from_string("geotiff") == FormatIdentifier.GEOTIFF

    def test_unknown_identifier_raises(self):
        with pytest.raises(UnknownFormatError, match="Unknown format identifier 'not_a_format'"):
            FormatIdentifier("not_a_format")

    def test_constant_shorthand(self):
        assert FormatIdentifier.GEOTIFF == FormatIdentifier("geotiff")
        assert FormatIdentifier.RASTER == FormatIdentifier("raster")
        assert FormatIdentifier.COG == FormatIdentifier("cog")


class TestStringRepr:
    def test_str(self):
        assert str(FormatIdentifier("geotiff")) == "geotiff"

    def test_repr(self):
        assert "FormatIdentifier" in repr(FormatIdentifier("geotiff"))
        assert "geotiff" in repr(FormatIdentifier("geotiff"))


class TestEqualityHash:
    def test_equality(self):
        a = FormatIdentifier("geotiff")
        b = FormatIdentifier("geotiff")
        c = FormatIdentifier("cog")
        assert a == b
        assert a != c
        assert a != "geotiff"

    def test_hash(self):
        a = FormatIdentifier("geotiff")
        b = FormatIdentifier("geotiff")
        assert hash(a) == hash(b)
        d = {a: "found"}
        assert d[b] == "found"

    def test_sortable(self):
        ids = [FormatIdentifier("cog"), FormatIdentifier("geotiff"), FormatIdentifier("dem")]
        sorted_ids = sorted(ids)
        assert [fi.value for fi in sorted_ids] == ["cog", "dem", "geotiff"]


class TestTaxonomy:
    def test_abstract_format_has_children(self):
        raster = FormatIdentifier("raster")
        assert raster.is_abstract
        assert len(raster.children) > 0
        assert FormatIdentifier("geotiff") in raster.children

    def test_concrete_format_no_children(self):
        gml = FormatIdentifier("gml")
        assert not gml.is_abstract
        assert gml.children == []

    def test_parent(self):
        assert FormatIdentifier("geotiff").parent == FormatIdentifier("raster")
        assert FormatIdentifier("cog").parent == FormatIdentifier("geotiff")
        assert FormatIdentifier("raster").parent == FormatIdentifier("gis_data")
        assert FormatIdentifier("gis_data").parent is None

    def test_lineage(self):
        cog = FormatIdentifier("cog")
        lineage = cog.lineage
        assert lineage == [FormatIdentifier("geotiff"), FormatIdentifier("raster"), FormatIdentifier("gis_data")]

    def test_leaves(self):
        raster = FormatIdentifier("raster")
        leaves = raster.leaves
        assert FormatIdentifier("cog") in leaves
        assert FormatIdentifier("geotiff") not in leaves  # geotiff has children (cog)
        # vector is not under raster
        assert FormatIdentifier("shapefile") not in leaves

    def test_vector_leaves(self):
        vector = FormatIdentifier("vector")
        leaves = vector.leaves
        assert FormatIdentifier("shapefile") in leaves
        assert FormatIdentifier("geojson") in leaves
        assert FormatIdentifier("geoparquet") in leaves

    def test_gis_data_leaves(self):
        gis = FormatIdentifier("gis_data")
        leaves = gis.leaves
        assert FormatIdentifier("cog") in leaves
        assert FormatIdentifier("shapefile") in leaves
        assert FormatIdentifier("csv") in leaves


class TestCatalog:
    def test_all_identifiers(self):
        all_ids = FormatIdentifier.all_identifiers()
        assert len(all_ids) > 20
        assert FormatIdentifier("geotiff") in all_ids

    def test_all_values(self):
        values = FormatIdentifier.all_values()
        assert "geotiff" in values
        assert "cog" in values
        assert "vector" in values
