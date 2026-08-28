"""Strongly-typed format identifier with singleton-like behavior.

Each distinct format instance only exists once. Format identifiers are case-insensitive. All registered formats are stored
in a module-level dictionary, enabling consumers to add their own identifiers.

Members:
    ::label(): Human-readable label.
    ::category(): Broad category (raster, vector, hybrid, tabular, abstract).
    ::description(): Short description.
    ::parent(): Immediate parent ``FormatIdentifier`` or ``None``.
"""
import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class FormatIdentifier:
    """Singleton-like format identifier.

    Creating ``FormatIdentifier("GeoTIFF")`` multiple times returns the *same*
    object. New labels are automatically registered and can be discovered via
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
        label: str,
        description: Optional[str] = None,
        children_labels: Optional[List[str]] = None,
        is_abstract: bool = False,
    ) -> "FormatIdentifier":
        label = label.strip()
        if not label:
            raise ValueError("FormatIdentifier label must be non-empty")

        # Prefer exact match first, then fall back to case-insensitive lookup
        existing = FormatIdentifier._REGISTRY.get(label.lower())
        if existing is not None:
            return existing

        instance = super().__new__(cls)
        FormatIdentifier._REGISTRY[label.lower()] = instance
        return instance

    def __init__(
        self,
        label: str,
        description: Optional[str] = None,
        children_labels: Optional[List[str]] = None,
        is_abstract: bool = False,
    ) -> None:
        # Avoid re-initialising an already-seen singleton.
        if hasattr(self, "_label"):
            return
        self._label = label.strip()
        self._description = description or ""
        self._children_labels = list(map(str.lower, children_labels)) if children_labels else []
        self._is_abstract = bool(is_abstract)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def value(self) -> str:
        """Human-readable label (backward-compatible alias)."""
        return self._label

    @property
    def label(self) -> str:
        """Human-readable label."""
        return self._label

    @property
    def description(self) -> str:
        return self._description

    @property
    def is_abstract(self) -> bool:
        return self._is_abstract

    @property
    def children(self) -> List["FormatIdentifier"]:
        """Immediate child formats."""
        result: List[FormatIdentifier] = []
        for child_label in self._children_labels:
            child = FormatIdentifier._REGISTRY.get(child_label.lower())
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
            if self._label.lower() in fi._children_labels:
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
            if child._label in visited:
                continue
            visited.add(child._label)
            child_kids = child.children
            if not child.is_abstract:
                result.append(child)
            if child_kids:
                stack.extend(child_kids)
        return result

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return self._label

    def __repr__(self) -> str:
        return f"FormatIdentifier({self._label!r} label={self._label!r})"

    def __hash__(self) -> int:
        return hash(self._label)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FormatIdentifier):
            return False
        return self._label == other._label

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, FormatIdentifier):
            return NotImplemented
        return self._label < other._label

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------

    @classmethod
    def all(cls) -> List["FormatIdentifier"]:
        """Return all registered format identifiers sorted by label."""
        return sorted(FormatIdentifier._REGISTRY.values(), key=lambda fi: fi._label)

    @classmethod
    def get(cls, label: str) -> Optional["FormatIdentifier"]:
        """Lookup a registered format by label (case-insensitive)."""
        existing = FormatIdentifier._REGISTRY.get(label.lower())
        return existing

    @classmethod
    def clear_registry(cls) -> None:
        """Remove *all* formats from the registry.  Useful for testing."""
        FormatIdentifier._REGISTRY.clear()


# ------------------------------------------------------------------
# Built-in canonical instances
# ------------------------------------------------------------------

FormatIdentifier.GIS = FormatIdentifier(
    "Geographical Information System Data",
    description="Geographical Information System (GIS) data encompasses various formats and types of data that represent geographic features and their attributes, enabling spatial analysis and visualization.",
    children_labels=["Raster Format", "Vector Format"],
    is_abstract=True,
)

FormatIdentifier.RASTER = FormatIdentifier(
    "Raster Format",
    description="Raster formats are used to represent spatial data in a grid of pixels or cells, where each pixel has a value representing information, such as color or elevation.",
    children_labels=["GeoTIFF", "DEM", "DSM", "DTM", "GRIB", "NetCDF", "GeoPackage"],
    is_abstract=True,
)

FormatIdentifier.VECTOR = FormatIdentifier(
    "Vector Format",
    description="Vector formats are used to represent spatial data using geometric shapes such as points, lines, and polygons, which are defined by coordinates.",
    children_labels=["Shapefile", "GeoJSON", "GeoPackage", "GeoParquet", "GML", "GPX", "KML", "WKT"],
    is_abstract=True,
)

FormatIdentifier.GEOTIFF = FormatIdentifier(
    "GeoTIFF",
    description="GeoTIFF is a public domain metadata standard which allows georeferencing information to be embedded within a TIFF file.",
    children_labels=["COG"],
    is_abstract=False,
)

FormatIdentifier.COG = FormatIdentifier(
    "COG",
    description="Cloud Optimized GeoTIFF (COG) is a regular GeoTIFF file that is organized in such a way that it can be efficiently streamed from HTTP-based web servers.",
)

FormatIdentifier.DEM = FormatIdentifier(
    "DEM",
    description="Digital Elevation Model (DEM) is a 3D representation of a terrain's surface created from terrain elevation data.",
)

FormatIdentifier.DSM = FormatIdentifier(
    "DSM",
    description="Digital Surface Model (DSM) represents the Earth's surface and includes all objects on it.",
)

FormatIdentifier.DTM = FormatIdentifier(
    "DTM",
    description="Digital Terrain Model (DTM) represents the bare ground surface without any objects like plants and buildings.",
)

FormatIdentifier.GRIB = FormatIdentifier(
    "GRIB",
    description="GRIB (GRIdded Binary or General Regularly-distributed Information in Binary form) is a concise data format commonly used in meteorology to store historical and forecast weather data.",
)

FormatIdentifier.NETCDF = FormatIdentifier(
    "NetCDF",
    description="NetCDF (Network Common Data Form) is a set of software libraries and machine-independent data formats that support the creation, access, and sharing of array-oriented scientific data.",
)

FormatIdentifier.SHAPEFILE = FormatIdentifier(
    "Shapefile",
    description="Shapefile is a popular geospatial vector data format for geographic information system (GIS) software.",
)

FormatIdentifier.GEOJSON = FormatIdentifier(
    "GeoJSON",
    description="GeoJSON is an open standard format designed for representing simple geographical features, along with their non-spatial attributes, based on JavaScript Object Notation (JSON).",
)

FormatIdentifier.GEOPACKAGE = FormatIdentifier(
    "GeoPackage",
    description="GeoPackage is an open, standards-based, platform-independent, portable, self-describing, compact format for transferring geospatial information.",
)

FormatIdentifier.GEOPARQUET = FormatIdentifier(
    "GeoParquet",
    description="GeoParquet is an open-source project that extends the Apache Parquet columnar storage format to support geospatial data types and operations.",
)

FormatIdentifier.GML = FormatIdentifier(
    "GML",
    description="Geography Markup Language (GML) is an XML grammar defined by the Open Geospatial Consortium (OGC) to express geographical features.",
)

FormatIdentifier.GPX = FormatIdentifier(
    "GPX",
    description="GPS Exchange Format (GPX) is an XML schema designed as a common GPS data format for software applications.",
)

FormatIdentifier.KML = FormatIdentifier(
    "KML",
    description="Keyhole Markup Language (KML) is an XML notation for expressing geographic annotation and visualization within Internet-based, two-dimensional maps and three-dimensional Earth browsers.",
)

FormatIdentifier.WKT = FormatIdentifier(
    "WKT",
    description="Well-Known Text (WKT) is a text markup language for representing vector geometry objects on a map.",
)

FormatIdentifier.CSV = FormatIdentifier(
    "CSV",
    description="Comma-Separated Values (CSV) is a simple file format used to store tabular data, such as a spreadsheet or database.",
)
