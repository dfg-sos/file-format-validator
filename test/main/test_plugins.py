"""Tests for loading validators from entry-point plugins."""
import importlib.metadata
import logging
import sys
import textwrap

import pytest

from format_validator.model import FormatIdentifier
from format_validator.registry import (
    PLUGIN_ENTRY_POINT_GROUP,
    DuplicateRegistrationError,
    registry,
)

PLUGIN_TEMPLATE = '''
from typing import List
from format_validator.model import FileFormatValidator, ValidationRequest, ValidationResult
from format_validator.registry import registry


@registry.register("{identifier}")
class PluginValidator(FileFormatValidator):
    def get_extensions(self) -> List[str]:
        return [".plugin"]

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        return ValidationResult.success(request)
'''


@pytest.fixture
def reset_registry():
    original_id = dict(registry._id_to_validators)
    original_cls = dict(registry._validators_to_id)
    yield
    registry._id_to_validators.clear()
    registry._validators_to_id.clear()
    registry._id_to_validators.update(original_id)
    registry._validators_to_id.update(original_cls)


@pytest.fixture
def plugins(tmp_path, monkeypatch, reset_registry):
    """Writes plugin modules to a temporary path and advertises them as entry points."""
    monkeypatch.syspath_prepend(str(tmp_path))
    entry_points = []
    module_names = []

    def add(name: str, source: str) -> None:
        module_name = f"test_plugin_{name}"
        (tmp_path / f"{module_name}.py").write_text(textwrap.dedent(source))
        entry_points.append(
            importlib.metadata.EntryPoint(name=name, value=module_name, group=PLUGIN_ENTRY_POINT_GROUP)
        )
        module_names.append(module_name)

    def fake_entry_points(group):
        return [ep for ep in entry_points if ep.group == group]

    monkeypatch.setattr("format_validator.registry.importlib.metadata.entry_points", fake_entry_points)
    yield add
    for module_name in module_names:
        sys.modules.pop(module_name, None)


class TestLoadPlugins:
    def test_registers_plugin_validator(self, plugins):
        plugins("bio", PLUGIN_TEMPLATE.format(identifier="test_fasta"))
        assert registry.load_plugins() == ["bio"]
        validator = registry.get_validator_class(FormatIdentifier("test_fasta"))
        assert validator is not None
        assert validator.__name__ == "PluginValidator"

    def test_no_plugins(self, plugins):
        assert registry.load_plugins() == []

    def test_broken_plugin_is_skipped(self, plugins, caplog):
        plugins("broken", "raise ImportError('missing native dependency')")
        plugins("bio", PLUGIN_TEMPLATE.format(identifier="test_fasta"))
        with caplog.at_level(logging.ERROR, logger="format_validator.registry"):
            assert registry.load_plugins() == ["bio"]
        assert "broken" in caplog.text
        assert FormatIdentifier("test_fasta") in registry.get_registered_identifiers()

    def test_duplicate_identifier_raises(self, plugins):
        plugins("clash", PLUGIN_TEMPLATE.format(identifier=FormatIdentifier.GEOTIFF.id))
        with pytest.raises(DuplicateRegistrationError, match="already registered"):
            registry.load_plugins()

    def test_duplicate_between_plugins_raises(self, plugins):
        plugins("first", PLUGIN_TEMPLATE.format(identifier="test_fasta"))
        plugins("second", PLUGIN_TEMPLATE.format(identifier="test_fasta"))
        with pytest.raises(DuplicateRegistrationError, match="already registered"):
            registry.load_plugins()

    def test_loading_twice_is_idempotent(self, plugins):
        plugins("bio", PLUGIN_TEMPLATE.format(identifier="test_fasta"))
        registry.load_plugins()
        assert registry.load_plugins() == ["bio"]

    def test_other_group_is_ignored(self, plugins):
        plugins("bio", PLUGIN_TEMPLATE.format(identifier="test_fasta"))
        assert registry.load_plugins(group="other.group") == []

    def test_duplicate_error_is_key_error(self):
        """Existing callers that catch KeyError keep working."""
        assert issubclass(DuplicateRegistrationError, KeyError)
