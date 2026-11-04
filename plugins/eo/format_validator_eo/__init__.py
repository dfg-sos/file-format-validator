"""EO plugin of the format validator: the EO format identifiers (``formats``) and their validators.

Installing this package registers the validators through the ``format_validator.validators``
entry point, so ``format_validator`` loads them on import.
"""
from . import formats
from .eo_file_format_validator import EOFileFormatValidator, EOMetadata
from .vector_file_validator import VectorFileValidator
from .raster_file_validator import RasterFileValidator

# Import concrete validators to trigger their @registry.register decorators
from .cog_validator import COGValidator
from .geojson_validator import GeoJSONValidator
from .geopackage_validator import GeoPackageValidator
from .geoparquet_validator import GeoParquetValidator
from .geotiff_validator import GeoTIFFValidator
from .gml_validator import GMLValidator
from .gpx_validator import GPXValidator
from .grib_validator import GRIBValidator
from .kml_validator import KMLValidator
from .netcdf_validator import NetCDFValidator
from .shapefile_validator import ShapefileValidator
from .wkt_validator import WKTValidator

__all__ = [
    "formats",
    "VectorFileValidator",
    "RasterFileValidator",
    "EOFileFormatValidator",
    "EOMetadata",
    "COGValidator",
    "GeoJSONValidator",
    "GeoPackageValidator",
    "GeoParquetValidator",
    "GeoTIFFValidator",
    "GMLValidator",
    "GPXValidator",
    "GRIBValidator",
    "KMLValidator",
    "NetCDFValidator",
    "ShapefileValidator",
    "WKTValidator",
]
