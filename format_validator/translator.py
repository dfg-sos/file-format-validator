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
        """Load the mapping from the ``mappings`` object of a JSON file. Other keys are ignored.

        If the file has an ``ontology_uri``, the keys of ``mappings`` are identifiers in that
        namespace, e.g. ``{"ontology_uri": "https://…/eo-formats#", "mappings": {"GeoTIFF": "GeoTIFF"}}``;
        otherwise they are full IRIs.

        Raises:
            ValueError: If an id is not a known ``FormatIdentifier``.
        """
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        namespace = data.get("ontology_uri", "")
        return cls({namespace + key: fid for key, fid in data["mappings"].items()})

    @classmethod
    def from_directory(cls, directory: Path) -> FormatTranslator:
        """Merge the mapping files (``*.json``, see :meth:`from_json`) of a directory, in name order.

        A missing or empty directory yields a translator without mappings.

        Raises:
            ValueError: If a file is not valid JSON, has no ``mappings`` object, maps to an unknown
                id, or maps an IRI to another id than an earlier file; the message names the file.
        """
        translator = cls({})
        for path in sorted(directory.glob("*.json")):
            try:
                translator |= cls.from_json(path)
            except KeyError as exc:
                raise ValueError(f"{path.name}: no {exc} object") from exc
            except ValueError as exc:
                raise ValueError(f"{path.name}: {exc}") from exc
        return translator

    def merge(self, other: FormatTranslator) -> FormatTranslator:
        """Merge two translators. An IRI may occur in both if it maps to the same format identifier.

        Raises:
            ValueError: If an IRI is mapped to different format identifiers.
        """
        conflicts = sorted(iri for iri, fi in other._to_local.items() if self._to_local.get(iri, fi) != fi)
        if conflicts:
            raise ValueError(f"Conflicting mappings for {conflicts}.")
        return FormatTranslator({iri: fi.id for iri, fi in (self._to_local | other._to_local).items()})

    def __or__(self, other: FormatTranslator) -> FormatTranslator:
        """Same as :meth:`merge`."""
        if not isinstance(other, FormatTranslator):
            return NotImplemented
        return self.merge(other)

    def to_local(self, iri: str) -> Optional[FormatIdentifier]:
        """The format identifier for an external IRI, or ``None`` if the IRI is not mapped."""
        return self._to_local.get(iri)

    def to_external(self, format_identifier: FormatIdentifier) -> Optional[str]:
        """The first external IRI mapped to the format identifier, or ``None``."""
        return next((iri for iri, fi in self._to_local.items() if fi == format_identifier), None)

    def iris(self) -> list[str]:
        """All mapped external IRIs."""
        return list(self._to_local)
