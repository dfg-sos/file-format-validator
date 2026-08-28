"""Format identifier translation layer.

Maps external ontology-specific format identifiers to module-local,
ontology-agnostic format identifiers.

- ``/path/to/mappings/<safe_uri>.json``     – per-ontology mappings (e.g. ``http---edamontology-org.json``).
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from format_validator.model.format_identifier import FormatIdentifier

logger = logging.getLogger(__name__)


class FormatTranslator:
    """Translate between external ontology format IDs and module-local IDs."""

    def __init__(self, mappings_dir: Path):
        self._ontology_mappings: Dict[str, Dict[str, str]] = {}
        self._load_ontology_mappings(mappings_dir)

    def _load_ontology_mappings(self, mappings_dir: Path) -> None:
        for path in mappings_dir.glob("*.json"):
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
        return None

    def get_loaded_ontologies(self) -> list[str]:
        return list(self._ontology_mappings.keys())
