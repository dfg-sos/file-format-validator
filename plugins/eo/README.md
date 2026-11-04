# EO Format Validator Plugin
Formats and validators for Earth observation data, as a plugin of the [format validator](../../README.md). Installing the package registers its formats and validators through the `format_validator.validators` entry point, so callers only use the core and refer to the formats by id:

```python
from pathlib import Path
from format_validator import FormatIdentifier, FileInput, ValidationMode, build_request, validate

raster = FormatIdentifier.get("GISRaster")  # None without this plugin
validate(build_request(raster, FileInput(path=Path("dem.tif")), ValidationMode.CONTENT))
```

The constants in [`format_validator_eo.eo_formats`](format_validator_eo/eo_formats.py), e.g. `eo_formats.GEOTIFF`, define the formats and their hierarchy for the plugin's own code.

## Formats
| Format | Id | Extensions | Parent |
|---|---|---|---|
| GeoTIFF | `GeoTIFF` | `.tif`, `.tiff` | `GISRaster` |
| Cloud Optimized GeoTIFF | `COG` | `.tif`, `.tiff` | `GeoTIFF` |
| DEM, DSM, DTM | `DEM`, `DSM`, `DTM` | `.tif`, `.tiff` | `GISRaster` |
| GRIB | `GRIB` | `.grib`, `.grib1`, `.grib2`, `.grb`, `.grb2`, `.gb` | `GISRaster` |
| NetCDF | `NetCDF` | `.nc`, `.nc4`, `.cdf` | `GISRaster` |
| GeoPackage | `GeoPackage` | `.gpkg` | `GISRaster`, `GISVector` |
| Shapefile | `Shapefile` | `.shp` | `GISVector` |
| GeoJSON | `GeoJSON` | `.geojson`, `.json` | `GISVector` |
| GeoParquet | `GeoParquet` | `.parquet`, `.geoparquet` | `GISVector` |
| GML | `GML` | `.gml`, `.xml` | `GISVector` |
| GPX | `GPX` | `.gpx` | `GISVector` |
| KML | `KML` | `.kml`, `.kmz` | `GISVector` |
| WKT | `WKT` | `.wkt`, `.txt` | `GISVector` |

The abstract formats `GIS`, `GISRaster` and `GISVector` group them. DEMs, DSMs and DTMs are validated as GeoTIFFs, since the file does not declare what its pixels hold. KML and WKT have no content reader and report `UNCERTAIN` in `CONTENT` mode.

## Metadata
Validators of this plugin use [EOMetadata](format_validator_eo/eo_file_format_validator.py) as metadata object:

| Key | Description | Formats |
|---|---|---|
| `crs` | Coordinate Reference System, any input of `pyproj.CRS.from_user_input`, e.g. `EPSG:4326` | all |
| `geometry_type` | Geometry type of a vector file, e.g. `Polygon` | vector formats |

## Requirements
GDAL, used through rasterio and fiona.
