# File Format Validator
Checks whether a file adheres to an expected format. Depending on the mode, the [validator](format_validator/validator.py) checks the file extension, opens the file and checks its metadata, or reads its whole content.

Formats are referenced by ontology-agnostic format identifiers, and external ontologies are mapped to them. The core is domain-agnostic and defines no formats: format identifiers, their hierarchy and validators come from [plugins](#writing-a-plugin). The [EO plugin](plugins/eo/README.md) provides formats for Earth observation data, e.g. GeoTIFF, NetCDF and GeoJSON, and is used in the examples below.

## Installation
Requires Python 3.13+. The core has no dependencies. Install it together with the plugins of your domains, e.g. `format-validator-eo`, which requires GDAL: on Python 3.13 the wheels of its dependencies bundle it, on 3.14 fiona has no wheel yet and is built against a system GDAL.

As a [command line tool](#command-line), with the EO plugin and without a system GDAL:

```sh
uv tool install --python 3.13 "format-validator @ git+https://github.com/dfg-sos/file-format-validator.git" \
  --with "format-validator-eo @ git+https://github.com/dfg-sos/file-format-validator.git#subdirectory=plugins/eo"
```

## Usage
Formats are referenced by their `FormatIdentifier`. Look one up by its id with `FormatIdentifier.get("GeoJSON")`, which returns `None` if no installed plugin defines it, or map an ontology IRI to it, see [Ontology Mappings](#ontology-mappings). Ids are case-insensitive, and each format exists once, so callers don't import a plugin to name its formats. Build a request with `build_request()`, then validate it with `validate()`:

```python
from pathlib import Path
from format_validator import FileInput, FormatIdentifier, InvalidRequest, ValidationMode, build_request, validate

geojson = FormatIdentifier.get("GeoJSON")  # None if no installed plugin defines it

try:
    request = build_request(
        geojson,
        FileInput(path=Path("buildings.geojson")),
        ValidationMode.METADATA,
        expected_metadata={"crs": "EPSG:4326", "geometry_type": "Polygon"},
    )
except InvalidRequest as exc:
    ...  # the request is wrong, e.g. return HTTP 400

result = validate(request)  # problems with the file are in the result
result.status               # ValidationStatus.SUCCESS, FAILURE or UNCERTAIN
result.to_json()            # status, request and events, each with a severity and cause
```

`build_request()` doesn't read the files, so you can check a request before writing uploads to disk. It raises a subclass of `InvalidRequest`:

| Error | Raised when |
|---|---|
| `UnsupportedFormat` | The format is `None`, e.g. an unknown id, or no validator is registered for the format or, for an abstract format, for any format below it |
| `UnsupportedMode` | The mode is not enabled for the request |
| `UnsupportedMetadataKeys` | A metadata key is not understood by the format's validator |
| `InvalidMetadataValue` | A metadata value cannot be parsed, e.g. an unknown CRS |

`validate()` returns a `ValidationResult` for every problem with the file. An unexpected exception inside a validator becomes an `UNCERTAIN` result. `supported_formats()` lists the formats the installed plugins can validate.

### Validation Modes
| Mode | File Extension | File Open, Metadata | Content |
|---|---|---|---|
| `BASIC` | &#10004; | &#10005; | &#10005; |
| `METADATA` | &#10004; | &#10004; | &#10005; |
| `CONTENT` | &#10004; | &#10004; | &#10004; |

`METADATA` reads only the header or declarations of a file (e.g. the CRS, the declared geometry type), so its cost does not grow with the file size. `CONTENT` also reads every pixel, feature or record: truncated or corrupt data fails, and every geometry must be compatible with the expected geometry type, not only the declared or sampled ones. It runs only if the metadata checks did not fail. Formats without a content reader report `UNCERTAIN` in `CONTENT` mode.

### Expected Metadata
`expected_metadata` holds plain strings. The validator of a format declares the keys it understands, and `build_request()` parses the values into the validator's metadata object, e.g. [EOMetadata](plugins/eo/README.md#metadata) with the CRS and geometry type of a GIS file. Empty values count as absent.

```python
from format_validator import FormatIdentifier, metadata_keys

metadata_keys(FormatIdentifier.get("GeoJSON"))  # frozenset({'crs', 'geometry_type'})
```

### Abstract Formats
Abstract formats group formats, e.g. `GISRaster`, `GISVector` and `GIS` of the EO plugin, and answer whether a file adheres to any of them. An abstract format covers the most general formats below it that have a validator. Their children refine them, e.g. a COG is a GeoTIFF, so they are not validated separately. A file is valid for an abstract format if it is valid for any of these formats whose extension matches, and the result names the format it is valid as. An abstract format accepts the metadata keys that all these formats understand.

## Ontology Mappings
The [FormatTranslator](format_validator/translator.py) converts external format IRIs, e.g. of the [SOS EO formats ontology](https://dfg-sos.github.io/ontologies/eo-formats), to format identifiers. You supply the mapping, with an explicit format identifier id for every IRI:

```python
from pathlib import Path
from format_validator import FormatTranslator

translator = FormatTranslator.from_json(Path("eo-formats.json"))  # {"mappings": {iri: id}}
translator.to_local("https://dfg-sos.github.io/ontologies/eo-formats#NetCDF_CF")  # FormatIdentifier('NetCDF')

translator = FormatTranslator.from_directory(Path("mappings"))  # all *.json files, merged
```

A mapping file has full IRIs as keys of `mappings`, or, if it gives an `ontology_uri`, the identifiers in that namespace: `{"ontology_uri": "https://dfg-sos.github.io/ontologies/eo-formats#", "mappings": {"NetCDF_CF": "NetCDF"}}`. Unknown ids raise a `ValueError` when the mapping is loaded. Translators merge with `a.merge(b)` or `a | b`. An IRI mapped to different ids raises a `ValueError`. See the EO plugin's [mapping](plugins/eo/tests/data/mappings/eo-formats.json), which is checked against a [copy of the ontology](plugins/eo/tests/data/ontologies/eo-formats.owl).

## Command Line
`format-validator validate` (or `python -m format_validator validate`) validates files against formats given as IRIs, translated by the mapping files of a directory (`--mappings DIR` or `$FORMAT_VALIDATOR_MAPPINGS`):

```sh
format-validator validate --mappings mappings/ \
  --format "https://dfg-sos.github.io/ontologies/eo-formats#NetCDF_CF" data/file.nc
format-validator validate --mappings mappings/ --format "<IRI>" --expect crs=EPSG:4326 \
  --secondary buildings.shx --secondary buildings.dbf buildings.shp     # multi-file format, expected metadata
format-validator validate --mappings mappings/ --manifest files.json   # several files, '-' reads stdin
```

`--mode` is `basic`, `metadata` (default) or `content`. Each line of the output starts with `format-validator:`, so it stands out in a shared log. `--color auto|always|never` colors it, by default only on a terminal and unless `$NO_COLOR` is set. `--json` prints the status and events of each file instead. A manifest names the files: `{"<name>": {"format": "<IRI>", "path": "data/file.nc", "secondary_paths": [], "expected_metadata": {}}}`, where `<name>` is any label that identifies the file in the output.

| Exit status | Meaning |
|---|---|
| `0` | every file `SUCCESS` or `UNCERTAIN` (`UNCERTAIN` is reported as a warning on stderr) |
| `1` | a file is `FAILURE`, or `ERROR`: it could not be validated, e.g. its format has no mapping |
| `2` | usage or configuration error (arguments, manifest, mappings); nothing was validated |

## Writing a Plugin
A plugin is a package with the formats and validators of a domain, like the [EO plugin](plugins/eo):

1. Define its `FormatIdentifier`s with their children. Children must refine their parent, i.e. a file valid as a child is valid as the parent too, since abstract formats skip the children of a format with a validator.
2. Implement a `FileFormatValidator` per format and register it with `@registry.register(...)`. One validator can be registered for several formats that the file cannot tell apart, e.g. `@registry.register(eo_formats.GEOTIFF, eo_formats.DEM, eo_formats.DSM, eo_formats.DTM)`. It runs once for an abstract format and reports all of them.
3. To accept expected metadata, override `metadata_keys()` and `parse_metadata()` on the validator base class of the domain.
4. Declare the module that registers the validators under the entry-point group `format_validator.validators` in its `pyproject.toml`:

```toml
[project.entry-points."format_validator.validators"]
bio = "format_validator_bio"
```

Importing `format_validator` loads all installed plugins, so their formats are known before mappings that refer to them are loaded. A plugin that fails to import is logged and skipped. A plugin that registers an identifier or validator class that is already taken raises a `DuplicateRegistrationError` (a `KeyError`). Plugins run in-process as trusted code.

## Development
The repository is a [uv](https://docs.astral.sh/uv/) workspace of the core and the [EO plugin](plugins/eo). To create a virtual environment with both and the development dependencies, run from the project root:

```sh
uv sync
uv run pytest  # core tests in test/, EO plugin tests in plugins/eo/tests/
```
