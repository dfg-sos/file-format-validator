"""Tests for the format identifier translation layer. The EO ontology mapping is tested in the EO plugin."""
import json
import pytest

from format_validator.translator import FormatTranslator
from format_validator.model import FormatIdentifier
from test.dummy_formats import BASE, GROUP, OTHER, REFINED

NS = "https://example.org/formats#"
MAPPING = {f"{NS}Base": "test_base", f"{NS}Group": "test_group", f"{NS}Other_Format": "test_other"}


@pytest.fixture
def translator():
    return FormatTranslator(MAPPING)


class TestFormatTranslator:
    def test_to_local(self, translator):
        assert translator.to_local(f"{NS}Base") is BASE
        assert translator.to_local(f"{NS}Group") is GROUP

    def test_to_local_where_fragment_and_id_differ(self, translator):
        assert translator.to_local(f"{NS}Other_Format") is OTHER

    @pytest.mark.parametrize("iri", [f"{NS}Unknown", "Base", "ns:Base"])
    def test_to_local_unmapped(self, translator, iri):
        assert translator.to_local(iri) is None

    def test_to_external(self, translator):
        assert translator.to_external(BASE) == f"{NS}Base"
        assert translator.to_external(OTHER) == f"{NS}Other_Format"

    def test_to_external_unmapped(self, translator):
        assert translator.to_external(REFINED) is None

    def test_from_json(self, tmp_path):
        path = tmp_path / "mapping.json"
        path.write_text(json.dumps({"ontology": f"{NS}", "mappings": MAPPING}))
        assert FormatTranslator.from_json(path).iris() == sorted(MAPPING)

    def test_ids_are_case_insensitive(self):
        translator = FormatTranslator({f"{NS}Base": "TEST_BASE"})
        assert translator.to_local(f"{NS}Base") is BASE

    def test_unknown_id_raises(self):
        with pytest.raises(ValueError, match="test_unknown_id"):
            FormatTranslator({f"{NS}Unknown": "test_unknown_id"})

    def test_unknown_id_creates_no_identifier(self):
        with pytest.raises(ValueError):
            FormatTranslator({f"{NS}Test": "test_translator_unknown"})
        assert FormatIdentifier.get("test_translator_unknown") is None

    def test_merge(self):
        merged = FormatTranslator({f"{NS}Base": "test_base"}) | FormatTranslator({f"{NS}Other_Format": "test_other"})
        assert merged.to_local(f"{NS}Base") is BASE
        assert merged.to_local(f"{NS}Other_Format") is OTHER

    def test_merge_same_mapping_twice(self):
        merged = FormatTranslator({f"{NS}Base": "test_base"}) | FormatTranslator({f"{NS}Base": "TEST_BASE"})
        assert merged.iris() == [f"{NS}Base"]

    def test_merge_method(self):
        merged = FormatTranslator({f"{NS}Base": "test_base"}).merge(FormatTranslator({f"{NS}Other_Format": "test_other"}))
        assert merged.iris() == [f"{NS}Base", f"{NS}Other_Format"]

    def test_merge_conflict_raises(self):
        with pytest.raises(ValueError, match="Group"):
            FormatTranslator({f"{NS}Group": "test_group"}) | FormatTranslator({f"{NS}Group": "test_base"})


def write_mapping(path, data):
    path.write_text(json.dumps(data))
    return path


class TestMappingFiles:
    def test_from_json_with_ontology_uri(self, tmp_path):
        path = write_mapping(tmp_path / "m.json", {"ontology_uri": NS, "mappings": {"Base": "test_base"}})
        assert FormatTranslator.from_json(path).to_local(f"{NS}Base") is BASE

    def test_from_directory_merges_files(self, tmp_path):
        write_mapping(tmp_path / "a.json", {"ontology_uri": NS, "mappings": {"Base": "test_base"}})
        write_mapping(tmp_path / "b.json", {"mappings": {f"{NS}Other_Format": "test_other"}})
        (tmp_path / "notes.txt").write_text("not a mapping")
        assert FormatTranslator.from_directory(tmp_path).iris() == [f"{NS}Base", f"{NS}Other_Format"]

    @pytest.mark.parametrize("directory", ["empty", "absent"])
    def test_from_directory_without_files(self, tmp_path, directory):
        (tmp_path / "empty").mkdir()
        assert FormatTranslator.from_directory(tmp_path / directory).iris() == []

    def test_from_directory_conflict_names_the_file(self, tmp_path):
        write_mapping(tmp_path / "a.json", {"mappings": {f"{NS}Group": "test_group"}})
        write_mapping(tmp_path / "b.json", {"mappings": {f"{NS}Group": "test_base"}})
        with pytest.raises(ValueError, match="b.json: Conflicting"):
            FormatTranslator.from_directory(tmp_path)

    @pytest.mark.parametrize(
        "content, match",
        [("{not json", "bad.json"), ('{"ontology_uri": "x"}', "bad.json: no 'mappings'"),
         ('{"mappings": {"x": "test_unknown_id"}}', "bad.json: .*test_unknown_id")],
    )
    def test_from_directory_invalid_file_names_the_file(self, tmp_path, content, match):
        (tmp_path / "bad.json").write_text(content)
        with pytest.raises(ValueError, match=match):
            FormatTranslator.from_directory(tmp_path)
