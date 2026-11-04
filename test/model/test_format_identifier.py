"""Tests for the FormatIdentifier value object."""
from format_validator.model.format_identifier import FormatIdentifier
from test.dummy_formats import GROUP, BASE, REFINED, OTHER, INNER, NESTED


class TestStringRepr:
    def test_str(self):
        assert str(BASE) == "test_base"

    def test_repr(self):
        assert repr(BASE) == "FormatIdentifier('test_base')"


class TestEqualityHash:
    def test_equality(self):
        assert BASE == FormatIdentifier("test_base")
        assert BASE != OTHER
        assert BASE != "test_base"

    def test_hash(self):
        d = {BASE: "found"}
        assert d[FormatIdentifier("test_base")] == "found"


class TestSingleton:
    def test_same_instance(self):
        assert FormatIdentifier("test_base") is BASE

    def test_case_insensitive(self):
        assert FormatIdentifier("TEST_BASE") is BASE
        assert FormatIdentifier.get(" Test_Base ") is BASE

    def test_new_format_registered(self):
        custom = FormatIdentifier("CustomFormat", is_abstract=False)
        assert FormatIdentifier.get("CustomFormat") is custom
        assert custom in FormatIdentifier.all()

    def test_reuse_existing(self):
        first = FormatIdentifier("ReuseMe")
        second = FormatIdentifier("ReuseMe", is_abstract=True)
        assert first is second
        assert not second.is_abstract  # first definition wins


class TestTaxonomy:
    def test_abstract_format_has_children(self):
        assert GROUP.is_abstract
        assert GROUP.children == [BASE, OTHER, INNER]

    def test_concrete_format_no_children(self):
        assert not OTHER.is_abstract
        assert OTHER.children == []

    def test_concrete_format_with_children(self):
        assert not BASE.is_abstract
        assert BASE.children == [REFINED]

    def test_parent(self):
        assert BASE.parent == GROUP
        assert REFINED.parent == BASE
        assert GROUP.parent is None

    def test_format_with_two_parents(self):
        assert set(OTHER.parents) == {GROUP, INNER}

    def test_leaves(self):
        # Concrete formats are leaves even with children, abstract ones never are.
        assert set(GROUP.leaves) == {BASE, REFINED, OTHER, NESTED}

    def test_expand_abstract(self):
        assert GROUP.expand() == GROUP.leaves

    def test_expand_concrete(self):
        assert BASE.expand() == [BASE]

    def test_all_returns_sorted(self):
        ids = [f.id for f in FormatIdentifier.all()]
        assert ids == sorted(ids)
        assert BASE in FormatIdentifier.all()
