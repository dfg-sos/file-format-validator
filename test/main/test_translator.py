"""Tests for the format identifier translation layer, against a copy of the SOS EO formats ontology."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

from format_validator.translator import FormatTranslator
from format_validator.model import FormatIdentifier


ONTOLOGY = Path("test/data/ontologies/eo-formats.owl")
MAPPING = Path("test/data/mappings/eo-formats.json")
EO = "https://dfg-sos.github.io/ontologies/eo-formats#"

RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"
OWL = "{http://www.w3.org/2002/07/owl#}"


def ontology_classes() -> dict[str, set[str]]:
    """IRI of each class in the ontology copy, with the IRIs of its direct superclasses."""
    root = ET.parse(ONTOLOGY).getroot()
    return {
        cls.attrib[f"{RDF}about"]: {sup.attrib[f"{RDF}resource"] for sup in cls.findall(f"{RDFS}subClassOf")}
        for cls in root.findall(f"{OWL}Class")
    }


@pytest.fixture
def translator():
    return FormatTranslator.from_json(MAPPING)


class TestFormatTranslator:
    def test_to_local(self, translator):
        assert translator.to_local(f"{EO}GeoTIFF") is FormatIdentifier.GEOTIFF
        assert translator.to_local(f"{EO}Shapefile") is FormatIdentifier.SHAPEFILE

    @pytest.mark.parametrize(
        "fragment, expected",
        [
            ("GIS", FormatIdentifier.GIS),
            ("Raster", FormatIdentifier.RASTER),
            ("Vector", FormatIdentifier.VECTOR),
            ("NetCDF_CF", FormatIdentifier.NETCDF),
        ],
    )
    def test_to_local_where_fragment_and_id_differ(self, translator, fragment, expected):
        assert translator.to_local(f"{EO}{fragment}") is expected

    @pytest.mark.parametrize("iri", [f"{EO}VRT", f"{EO}Unknown", "GeoTIFF", "eo:GeoTIFF"])
    def test_to_local_unmapped(self, translator, iri):
        assert translator.to_local(iri) is None

    def test_to_external(self, translator):
        assert translator.to_external(FormatIdentifier.GEOTIFF) == f"{EO}GeoTIFF"
        assert translator.to_external(FormatIdentifier.NETCDF) == f"{EO}NetCDF_CF"

    def test_to_external_unmapped(self, translator):
        assert translator.to_external(FormatIdentifier.CSV) is None

    def test_ids_are_case_insensitive(self):
        translator = FormatTranslator({f"{EO}GeoTIFF": "geotiff"})
        assert translator.to_local(f"{EO}GeoTIFF") is FormatIdentifier.GEOTIFF

    def test_unknown_id_raises(self):
        with pytest.raises(ValueError, match="raster"):
            FormatTranslator({f"{EO}Raster": "raster"})

    def test_unknown_id_creates_no_identifier(self):
        with pytest.raises(ValueError):
            FormatTranslator({f"{EO}Test": "test_translator_unknown"})
        assert FormatIdentifier.get("test_translator_unknown") is None


class TestEOFormatsMapping:
    """The test mapping against the ontology copy."""

    def test_mapped_iris_exist_in_ontology(self, translator):
        assert set(translator.iris()) <= set(ontology_classes())

    def test_maps_every_ontology_class_with_a_local_validator(self, translator):
        # Ontology classes without a local identifier are known to be unsupported.
        unmapped = {iri.removeprefix(EO) for iri in ontology_classes() if translator.to_local(iri) is None}
        assert unmapped == {"EsriJSON", "GeoZarr", "OSM_JSON", "OSM_XML", "PBF", "VRT", "WKB", "XDMF"}

    def test_hierarchy_matches_ontology(self, translator):
        # Every subClassOf between mapped classes is a parent-child relation of the format identifiers.
        for iri, superclasses in ontology_classes().items():
            child = translator.to_local(iri)
            for superclass in superclasses:
                parent = translator.to_local(superclass)
                if child and parent:
                    assert child in parent.children, f"{child} is not a child of {parent}"

    def test_children_are_subclasses_in_ontology(self, translator):
        classes = ontology_classes()
        for iri in translator.iris():
            parent = translator.to_local(iri)
            for child in parent.children:
                child_iri = translator.to_external(child)
                assert child_iri is not None, f"{child} is not mapped"
                assert iri in classes[child_iri], f"{child_iri} is not a subclass of {iri}"

    def test_mapping_file_is_for_the_ontology_copy(self):
        data = json.loads(MAPPING.read_text())
        root = ET.parse(ONTOLOGY).getroot()
        ontology = root.find(f"{OWL}Ontology")
        assert data["ontology"] == ontology.attrib[f"{RDF}about"]
        assert data["version"] == ontology.find(f"{OWL}versionInfo").text
