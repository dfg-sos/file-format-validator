"""Format identifier translation layer.

Maps external ontology-specific format identifiers to module-local,
ontology-agnostic format identifiers.

Mapping files are stored in ``eo_format_validator/mappings/``:
- ``formats.json``       – canonical local identifiers.
- ``<safe_uri>.json``  – per-ontology mappings (e.g. ``http---edamontology-org.json``).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from eo_format_validator.model.format_identifier import FormatIdentifier
from importlib import resources

logger = logging.getLogger(__name__)


class FormatTranslator:
    """Translate between external ontology format IDs and module-local IDs."""

    def __init__(self, package_root: Optional[Path] = None, mappings_dir: Optional[Path] = None):
        if package_root is None:
            package_root = Path(resources.files("eo_format_validator"))  # type: ignore[arg-type]
        if mappings_dir is None:
            mappings_dir = package_root / "mappings"
        self._package_root = Path(package_root)
        self._mappings_dir = Path(mappings_dir)
        self._local_metadata: Dict[str, dict] = {}
        self._ontology_mappings: Dict[str, Dict[str, str]] = {}
        self._load_local()
        self._load_ontology_mappings()

    def _load_local(self) -> None:
        local_path = self._package_root / "formats.json"
        if not local_path.exists():
            logger.warning("formats.json not found in %s", self._package_root)
            return
        with local_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._local_metadata = data.get("formats", {})
        logger.debug("Loaded %d local format definitions", len(self._local_metadata))

    def _load_ontology_mappings(self) -> None:
        for path in self._mappings_dir.glob("*.json"):
            if path.name == "formats.json":
                continue
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            ontology_uri = data.get("ontology_uri", self._path_to_uri(path.stem))
            mappings: Dict[str, str] = data.get("mappings", {})
            self._ontology_mappings[ontology_uri] = mappings
            logger.debug(
                "Loaded mapping for ontology '%s' with %d entries", ontology_uri, len(mappings)
            )

    @staticmethod
    def _path_to_uri(stem: str) -> str:
        return stem.replace("---", "://").replace("--", "/")

    @staticmethod
    def _uri_to_path(uri: str) -> str:
        return uri.replace("://", "---").replace("/", "--")

    @staticmethod
    def _strip_uri_prefix(fmt: str) -> str:
        if fmt.startswith("http://") or fmt.startswith("https://"):
            without_protocol = fmt.split("://", 1)[-1]
            parts = without_protocol.split("/")
            for part in reversed(parts):
                if part:
                    return part
        if ":" in fmt:
            return fmt.split(":", 1)[-1]
        return fmt

    def to_local(self, external_id: str, ontology_uri: Optional[str] = None) -> Optional[FormatIdentifier]:
        stripped = self._strip_uri_prefix(external_id)
        if ontology_uri:
            mapping = self._ontology_mappings.get(ontology_uri, {})
            if stripped in mapping:
                return FormatIdentifier(mapping[stripped])
        for mapping in self._ontology_mappings.values():
            if stripped in mapping:
                return FormatIdentifier(mapping[stripped])
        if stripped in self._local_metadata:
            return FormatIdentifier(stripped)
        logger.debug("No mapping found for '%s' (stripped: '%s')", external_id, stripped)
        return None

    def to_external(self, local_id: str, ontology_uri: str) -> Optional[str]:
        if ontology_uri not in self._ontology_mappings:
            logger.warning("Ontology '%s' not loaded", ontology_uri)
            return None
        mapping = self._ontology_mappings[ontology_uri]
        for ext_id, loc_id in mapping.items():
            if loc_id == local_id:
                return ext_id
        return local_id if local_id in self._local_metadata else None

    def get_loaded_ontologies(self) -> list[str]:
        return list(self._ontology_mappings.keys())

    def get_local_formats(self) -> list[FormatIdentifier]:
        return [FormatIdentifier(k) for k in self._local_metadata.keys()]

    def get_local_metadata(self, local_id: str | FormatIdentifier) -> Optional[dict]:
        if isinstance(local_id, FormatIdentifier):
            local_id = local_id.value
        return self._local_metadata.get(local_id)


translator = FormatTranslator()
