# EO Format Validator Plugin
Formats and validators for Earth observation data, as a plugin of the [format validator](../../README.md). Installing the package registers its validators through the `format_validator.validators` entry point. Its format identifiers are in [`format_validator_eo.formats`](format_validator_eo/formats.py):

```python
from pathlib import Path
from format_validator import build_request, validate, FileInput, ValidationMode
from format_validator_eo import formats

validate(build_request(formats.RASTER, FileInput(path=Path("dem.tif")), ValidationMode.CONTENT))
```

## Formats
| Format | Identifier | Extensions | Parent |
|---|---|---|---|
| GeoTIFF | `GEOTIFF` | `.tif`, `.tiff` | `GISRaster` |
| Cloud Optimized GeoTIFF | `COG` | `.tif`, `.tiff` | `GeoTIFF` |
| DEM, DSM, DTM | `DEM`, `DSM`, `DTM` | `.tif`, `.tiff` | `GISRaster` |
| GRIB | `GRIB` | `.grib`, `.grib1`, `.grib2`, `.grb`, `.grb2`, `.gb` | `GISRaster` |
| NetCDF | `NETCDF` | `.nc`, `.nc4`, `.cdf` | `GISRaster` |
| GeoPackage | `GEOPACKAGE` | `.gpkg` | `GISRaster`, `GISVector` |
| Shapefile | `SHAPEFILE` | `.shp` | `GISVector` |
| GeoJSON | `GEOJSON` | `.geojson`, `.json` | `GISVector` |
| GeoParquet | `GEOPARQUET` | `.parquet`, `.geoparquet` | `GISVector` |
| GML | `GML` | `.gml`, `.xml` | `GISVector` |
| GPX | `GPX` | `.gpx` | `GISVector` |
| KML | `KML` | `.kml`, `.kmz` | `GISVector` |
| WKT | `WKT` | `.wkt`, `.txt` | `GISVector` |

The abstract formats `GIS`, `GISRaster` (`RASTER`) and `GISVector` (`VECTOR`) group them. DEMs, DSMs and DTMs are validated as GeoTIFFs, since the file does not declare what its pixels hold. KML and WKT have no content reader and report `UNCERTAIN` in `CONTENT` mode.

## Metadata
Validators of this plugin use [EOMetadata](format_validator_eo/eo_file_format_validator.py) as metadata object:

| Key | Description | Formats |
|---|---|---|
| `crs` | Coordinate Reference System, any input of `pyproj.CRS.from_user_input`, e.g. `EPSG:4326` | all |
| `geometry_type` | Geometry type of a vector file, e.g. `Polygon` | vector formats |

## Requirements
GDAL, used through rasterio and fiona.
