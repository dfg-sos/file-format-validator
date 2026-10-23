"""Format identifier translation layer.

Maps external format IRIs, e.g. the classes of the SOS EO formats ontology, to module-local,
ontology-agnostic format identifiers. The caller supplies the mapping, with an explicit entry
for every IRI, for example as a JSON file::

    {
      "mappings": {
        "https://dfg-sos.github.io/ontologies/eo-formats#GeoTIFF": "GeoTIFF",
        "https://dfg-sos.github.io/ontologies/eo-formats#NetCDF_CF": "NetCDF"
      }
    }
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Mapping, Optional
from format_validator.model.format_identifier import FormatIdentifier


class FormatTranslator:
    """Translate between external format IRIs and module-local format identifiers."""

    def __init__(self, mapping: Mapping[str, str]):
        """
        Args:
            mapping: Format identifier id for each external IRI.

        Raises:
            ValueError: If an id is not a known ``FormatIdentifier``.
        """
        unknown = sorted({fid for fid in mapping.values() if FormatIdentifier.get(fid) is None})
        if unknown:
            raise ValueError(f"Mapping contains unknown format identifiers: {unknown}.")
        self._to_local: dict[str, FormatIdentifier] = {iri: FormatIdentifier(fid) for iri, fid in mapping.items()}

    @classmethod
    def from_json(cls, path: Path) -> FormatTranslator:
        """Load the mapping from the ``mappings`` object of a JSON file. Other keys are ignored."""
        with path.open("r", encoding="utf-8") as fh:
            return cls(json.load(fh)["mappings"])

    def to_local(self, iri: str) -> Optional[FormatIdentifier]:
        """The format identifier for an external IRI, or ``None`` if the IRI is not mapped."""
        return self._to_local.get(iri)

    def to_external(self, format_identifier: FormatIdentifier) -> Optional[str]:
        """The first external IRI mapped to the format identifier, or ``None``."""
        return next((iri for iri, fi in self._to_local.items() if fi == format_identifier), None)

    def iris(self) -> list[str]:
        """All mapped external IRIs."""
        return list(self._to_local)
