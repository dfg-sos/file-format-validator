"""Format identifiers of the EO domain and their hierarchy.

Children refine their parent: a file valid as a child is valid as the parent too (e.g. a COG is a
GeoTIFF). Abstract formats group formats, see ``format_validator.validate``.
"""
from format_validator.model import FormatIdentifier

GIS = FormatIdentifier("GIS", children_ids=["GISRaster", "GISVector"], is_abstract=True)
RASTER = FormatIdentifier("GISRaster", children_ids=["GeoTIFF", "DEM", "DSM", "DTM", "GRIB", "NetCDF", "GeoPackage"], is_abstract=True)
VECTOR = FormatIdentifier("GISVector", children_ids=["Shapefile", "GeoJSON", "GeoPackage", "GeoParquet", "GML", "GPX", "KML", "WKT"], is_abstract=True)
GEOTIFF = FormatIdentifier("GeoTIFF", children_ids=["COG"])
COG = FormatIdentifier("COG")
DEM = FormatIdentifier("DEM")
DSM = FormatIdentifier("DSM")
DTM = FormatIdentifier("DTM")
GRIB = FormatIdentifier("GRIB")
NETCDF = FormatIdentifier("NetCDF")
SHAPEFILE = FormatIdentifier("Shapefile")
GEOJSON = FormatIdentifier("GeoJSON")
GEOPACKAGE = FormatIdentifier("GeoPackage")
GEOPARQUET = FormatIdentifier("GeoParquet")
GML = FormatIdentifier("GML")
GPX = FormatIdentifier("GPX")
KML = FormatIdentifier("KML")
WKT = FormatIdentifier("WKT")
CSV = FormatIdentifier("CSV")
