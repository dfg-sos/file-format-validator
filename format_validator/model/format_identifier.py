"""Strongly-typed format identifier value object.

FormatIdentifier wraps a validated module-local format ID string.
Construction validates against the canonical formats.json catalog,
preventing accidental use of ontology-specific identifiers where
module-local IDs are expected.

Taxonomy traversal (parent, children, leaves) is built from the
parent/child relationships declared in formats.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from importlib import resources

logger = logging.getLogger(__name__)


class UnknownFormatError(ValueError):
    """Raised when attempting to construct a FormatIdentifier with an unknown ID."""
    pass


class FormatIdentifier:
    """Canonical, hashable, comparable format identifier.

    Usage::

        ident = FormatIdentifier("geotiff")   # OK
        ident = FormatIdentifier.GEOTIFF      # constant shortcut (also OK)
        ident = FormatIdentifier("format_4109")  # raises UnknownFormatError

    Attributes:
        value: The canonical local ID string (e.g. ``"geotiff"``).
        label: Human-readable label.
        category: Broad category (raster, vector, hybrid, tabular, abstract).
        description: Short description.
        parent: Immediate parent ``FormatIdentifier`` or ``None``.
    """

    _ALL: Dict[str, "FormatIdentifier"] = {}
    _CHILDREN: Dict[str, List["FormatIdentifier"]] = {}
    _LOADED: bool = False

    value: str
    label: str
    category: str
    description: str
    parent: Optional["FormatIdentifier"]

    # Instances are created by _Catalog.load() via object.__new__ +
    # object.__setattr__.  __init__ must be a no-op so that calling
    # FormatIdentifier("geotiff") (which triggers __new__ then __init__)
    # does NOT overwrite the cached attributes.
    def __init__(self, *args, **kwargs):  # type: ignore[no-redef]
        pass

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._LOADED:
            _Catalog.load()

    @classmethod
    def from_string(cls, raw: str) -> "FormatIdentifier":
        cls._ensure_loaded()
        ident = cls._ALL.get(raw)
        if ident is None:
            raise UnknownFormatError(
                f"Unknown format identifier '{raw}'. Known: {sorted(cls._ALL.keys())}"
            )
        return ident

    def __new__(cls, raw: str) -> "FormatIdentifier":
        cls._ensure_loaded()
        instance = cls._ALL.get(raw)
        if instance is None:
            raise UnknownFormatError(
                f"Unknown format identifier '{raw}'. Known: {sorted(cls._ALL.keys())}"
            )
        return instance
    
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"FormatIdentifier({self.value!r} label={self.label!r})"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FormatIdentifier):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, FormatIdentifier):
            return NotImplemented
        return self.value < other.value

    @property
    def is_abstract(self) -> bool:
        return bool(self._CHILDREN.get(self.value))

    @property
    def children(self) -> List["FormatIdentifier"]:
        return list(self._CHILDREN.get(self.value, []))

    @property
    def leaves(self) -> List["FormatIdentifier"]:
        result: List[FormatIdentifier] = []
        visited: Set[str] = set()
        stack = list(self.children)
        while stack:
            child = stack.pop()
            if child.value in visited:
                continue
            visited.add(child.value)
            child_kids = self._CHILDREN.get(child.value, [])
            if not child_kids:
                result.append(child)
            else:
                stack.extend(child_kids)
        return result

    @property
    def lineage(self) -> List["FormatIdentifier"]:
        result = []
        current = self.parent
        while current is not None:
            result.append(current)
            current = current.parent
        return result

    @classmethod
    def all_identifiers(cls) -> List["FormatIdentifier"]:
        cls._ensure_loaded()
        return list(cls._ALL.values())

    @classmethod
    def all_values(cls) -> List[str]:
        cls._ensure_loaded()
        return sorted(cls._ALL.keys())


class _Catalog:
    _loaded: bool = False

    @classmethod
    def load(cls, path: Optional[Path] = None) -> None:
        if cls._loaded:
            return
        cls._loaded = True  # Prevent re-entry during _install_constants
        FormatIdentifier._LOADED = True
        if path is None:
            path = Path(str(resources.files("format_validator") / "formats.json"))
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        formats_data = data.get("formats", {})

        for key, meta in formats_data.items():
            fi = object.__new__(FormatIdentifier)
            object.__setattr__(fi, "value", key)
            object.__setattr__(fi, "label", meta.get("label", key))
            object.__setattr__(fi, "category", meta.get("category", "unknown"))
            object.__setattr__(fi, "description", meta.get("description", ""))
            object.__setattr__(fi, "parent", None)
            FormatIdentifier._ALL[key] = fi

        for key, meta in formats_data.items():
            parent_key = meta.get("parent")
            if parent_key:
                fi = FormatIdentifier._ALL[key]
                parent_fi = FormatIdentifier._ALL.get(parent_key)
                object.__setattr__(fi, "parent", parent_fi)
                if parent_key not in FormatIdentifier._CHILDREN:
                    FormatIdentifier._CHILDREN[parent_key] = []
                FormatIdentifier._CHILDREN[parent_key].append(fi)

        logger.debug("Loaded %d format identifiers", len(FormatIdentifier._ALL))


def _install_constants() -> None:
    for key in sorted(FormatIdentifier._ALL.keys()):
        attr = key.upper().replace("-", "_")
        setattr(FormatIdentifier, attr, FormatIdentifier._ALL[key])


_Catalog.load()
_install_constants()
