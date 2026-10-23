"""Strongly-typed format identifier with singleton-like behavior.

Each distinct format instance only exists once. Format identifiers are case-insensitive. All registered formats are stored
in a module-level dictionary, enabling consumers to add their own identifiers.

Members:
    ::id: Identifier string.
    ::children: Immediate child ``FormatIdentifier``s.
    ::parent: Immediate parent ``FormatIdentifier`` or ``None``.
    ::leaves: All non-abstract descendants.
    ::expand(): The leaves of an abstract format, or the format itself.
"""
import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class FormatIdentifier:
    """Singleton-like format identifier.

    Creating ``FormatIdentifier("GeoTIFF")`` multiple times returns the *same*
    object. New identifiers are automatically registered and can be discovered via
    :meth:`all`.
    """

    # Module-level registry for singleton-like behaviour
    _REGISTRY: Dict[str, "FormatIdentifier"] = {}

    # -- forward declarations of canonical built-in instances (populated below) --
    GIS: "FormatIdentifier"
    RASTER: "FormatIdentifier"
    VECTOR: "FormatIdentifier"
    GEOTIFF: "FormatIdentifier"
    COG: "FormatIdentifier"
    DEM: "FormatIdentifier"
    DSM: "FormatIdentifier"
    DTM: "FormatIdentifier"
    GRIB: "FormatIdentifier"
    NETCDF: "FormatIdentifier"
    SHAPEFILE: "FormatIdentifier"
    GEOJSON: "FormatIdentifier"
    GEOPACKAGE: "FormatIdentifier"
    GEOPARQUET: "FormatIdentifier"
    GML: "FormatIdentifier"
    GPX: "FormatIdentifier"
    KML: "FormatIdentifier"
    WKT: "FormatIdentifier"
    CSV: "FormatIdentifier"

    def __new__(
        cls,
        id: str,
        children_ids: Optional[List[str]] = None,
        is_abstract: bool = False,
    ) -> "FormatIdentifier":
        id = id.strip()
        if not id:
            raise ValueError("FormatIdentifier id must be non-empty")

        existing = FormatIdentifier._REGISTRY.get(id.lower())
        if existing is not None:
            return existing

        instance = super().__new__(cls)
        FormatIdentifier._REGISTRY[id.lower()] = instance
        return instance

    def __init__(
        self,
        id: str,
        children_ids: Optional[List[str]] = None,
        is_abstract: bool = False,
    ) -> None:
        # Avoid re-initialising an already-seen singleton.
        if hasattr(self, "_id"):
            return
        self._id = id.strip()
        self._children_ids = list(map(str.lower, children_ids)) if children_ids else []
        self._is_abstract = bool(is_abstract)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_abstract(self) -> bool:
        return self._is_abstract

    @property
    def children(self) -> List["FormatIdentifier"]:
        """Immediate child formats."""
        result: List[FormatIdentifier] = []
        for child_id in self._children_ids:
            child = FormatIdentifier._REGISTRY.get(child_id)
            if child is not None:
                result.append(child)
        return result

    @property
    def parent(self) -> Optional["FormatIdentifier"]:
        return self.parents[0] if self.parents else None

    @property
    def parents(self) -> Optional[List["FormatIdentifier"]]:
        result: List[FormatIdentifier] = []
        for fi in FormatIdentifier._REGISTRY.values():
            if self._id.lower() in fi._children_ids:
                result.append(fi)
        return result if result else None

    @property
    def leaves(self) -> List["FormatIdentifier"]:
        """All non-abstract descendants."""
        result: List[FormatIdentifier] = []
        visited: Set[str] = set()
        stack = list(self.children)
        while stack:
            child = stack.pop()
            if child._id in visited:
                continue
            visited.add(child._id)
            child_kids = child.children
            if not child.is_abstract:
                result.append(child)
            if child_kids:
                stack.extend(child_kids)
        return result

    def expand(self) -> List["FormatIdentifier"]:
        """Expand an abstract format to all its leaves. A format that is not abstract expands to itself."""
        return self.leaves if self._is_abstract else [self]

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return f"FormatIdentifier({self._id!r})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FormatIdentifier):
            return False
        return self._id == other._id

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, FormatIdentifier):
            return NotImplemented
        return self._id < other._id

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------

    @classmethod
    def all(cls) -> List["FormatIdentifier"]:
        """Return all registered format identifiers sorted by id."""
        return sorted(FormatIdentifier._REGISTRY.values(), key=lambda fi: fi._id)

    @classmethod
    def get(cls, id: str) -> Optional["FormatIdentifier"]:
        """Lookup a registered format by id (case-insensitive)."""
        return FormatIdentifier._REGISTRY.get(id.strip().lower())

    @classmethod
    def clear_registry(cls) -> None:
        """Remove *all* formats from the registry.  Useful for testing."""
        FormatIdentifier._REGISTRY.clear()


# ------------------------------------------------------------------
# Built-in canonical instances
# ------------------------------------------------------------------

FormatIdentifier.GIS = FormatIdentifier("GIS", children_ids=["GISRaster", "GISVector"], is_abstract=True)
FormatIdentifier.RASTER = FormatIdentifier("GISRaster", children_ids=["GeoTIFF", "DEM", "DSM", "DTM", "GRIB", "NetCDF", "GeoPackage"], is_abstract=True)
FormatIdentifier.VECTOR = FormatIdentifier("GISVector", children_ids=["Shapefile", "GeoJSON", "GeoPackage", "GeoParquet", "GML", "GPX", "KML", "WKT"], is_abstract=True)
FormatIdentifier.GEOTIFF = FormatIdentifier("GeoTIFF", children_ids=["COG"])
FormatIdentifier.COG = FormatIdentifier("COG")
FormatIdentifier.DEM = FormatIdentifier("DEM")
FormatIdentifier.DSM = FormatIdentifier("DSM")
FormatIdentifier.DTM = FormatIdentifier("DTM")
FormatIdentifier.GRIB = FormatIdentifier("GRIB")
FormatIdentifier.NETCDF = FormatIdentifier("NetCDF")
FormatIdentifier.SHAPEFILE = FormatIdentifier("Shapefile")
FormatIdentifier.GEOJSON = FormatIdentifier("GeoJSON")
FormatIdentifier.GEOPACKAGE = FormatIdentifier("GeoPackage")
FormatIdentifier.GEOPARQUET = FormatIdentifier("GeoParquet")
FormatIdentifier.GML = FormatIdentifier("GML")
FormatIdentifier.GPX = FormatIdentifier("GPX")
FormatIdentifier.KML = FormatIdentifier("KML")
FormatIdentifier.WKT = FormatIdentifier("WKT")
FormatIdentifier.CSV = FormatIdentifier("CSV")
