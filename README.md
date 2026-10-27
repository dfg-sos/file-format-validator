# File Format Validator
This package provides a validation tool for file formats to examine a file according to a specified format. It provides ontology-agnostic format identifiers to uniquely reference different file formats. For existing ontologies a mapping to the internal formats can be supplied as a json file. For a supported format, the [Format Validator](format_validator/validator.py) can decide for a certain input file whether it adheres to that format specification. Depending on the selected mode, the file extension is validated, the file is opened, and additional metadata is validated. 

## Validation Modes
| Mode | File Extension | File Open | Metadata Validation|
|---|---|---|---|
| `BASIC` | &#10004; | &#10005; | &#10005; 
| `STRUCTURAL` | &#10004; | &#10004; | &#10005; 
| `FULL` | &#10004; | &#10004; | &#10004;

## Metadata Validation
Currently, only EO metadata validation is supported. The metadata is passed to a request by setting a sidecar *metadata object* to `ValidationRequest::metadata`
| Metadata Object | Attribute | Description 
|---|---|---|
| [EOMetadata](format_validator/validators/eo/eo_file_format_validator.py) | `crs` | Coordinate Reference System of GIS file 
| [EOMetadata](format_validator/validators/eo/eo_file_format_validator.py) | `geometry_type` | Geometry type of (GIS) vector file 

Callers don't need to build the metadata object themselves. The validator registered for a format declares the metadata keys it understands, and `build_request()` parses plain strings into its metadata object:

```python
from format_validator import FormatIdentifier, metadata_keys

metadata_keys(FormatIdentifier.GEOJSON)  # frozenset({'crs', 'geometry_type'})
```

Empty values count as absent. To support metadata for a new domain, override `metadata_keys()` and `parse_metadata()` on its validator base class.

## Abstract Formats
Abstract formats such as `FormatIdentifier.RASTER`, `VECTOR` and `GIS` group concrete formats. A file is valid for an abstract format if it is valid for any of its leaves (`FormatIdentifier.expand()`) whose extension matches. An abstract format accepts the metadata keys that all its leaves understand.

# Integration
Build a request with `build_request()`, then validate it with `validate()`:

```python
from pathlib import Path
from format_validator import (
    FileInput,
    FormatIdentifier,
    InvalidRequest,
    ValidationMode,
    ValidationRequest,
    ValidationResult,
    build_request,
    validate,
)

try:
    request: ValidationRequest = build_request(
        FormatIdentifier.GEOJSON,
        FileInput(path=Path("buildings.geojson")),
        ValidationMode.FULL,
        expected_metadata={"crs": "EPSG:4326", "geometry_type": "Polygon"},
    )
except InvalidRequest as exc:
    ...  # the request is wrong, e.g. return HTTP 400

result: ValidationResult = validate(request)  # problems with the file are in the result
result.status                                 # ValidationStatus.SUCCESS, FAILURE or UNCERTAIN
```

`build_request()` doesn't read the files, so you can check a request before writing uploads to disk. It raises a subclass of `InvalidRequest`:

| Error | Raised when |
|---|---|
| `UnsupportedFormat` | No validator is registered for the format or, for an abstract format, its leaves |
| `UnsupportedMode` | The mode is not enabled for the request |
| `UnsupportedMetadataKeys` | A metadata key is not understood by the format's validator |
| `InvalidMetadataValue` | A metadata value cannot be parsed, e.g. an unknown CRS |

`validate()` returns a `ValidationResult` for every problem with the file. An unexpected exception inside a validator becomes an `UNCERTAIN` result. `supported_formats()` lists the formats that can be validated.

## Ontology Mappings
The [FormatTranslator](format_validator/translator.py) converts external format IRIs, e.g. of the [SOS EO formats ontology](https://dfg-sos.github.io/ontologies/eo-formats), to format identifiers. You supply the mapping, with an explicit format identifier id for every IRI:

```python
from pathlib import Path
from format_validator import FormatTranslator

translator = FormatTranslator.from_json(Path("eo-formats.json"))   # {"mappings": {iri: id}}
translator.to_local("https://dfg-sos.github.io/ontologies/eo-formats#NetCDF_CF")  # FormatIdentifier.NETCDF
```

Unknown ids raise a `ValueError` when the mapping is loaded. Translators merge with `a.merge(b)` or `a | b`. An IRI mapped to different ids raises a `ValueError`. See the [test mapping](test/data/mappings/eo-formats.json), which is checked against a [copy of the ontology](test/data/ontologies/eo-formats.owl).

## Validator Plugins
Validators for other domains can ship as separate packages. A plugin package registers its validators with `@registry.register(...)` and declares the module that does so under the entry-point group `format_validator.validators` in its `pyproject.toml`:

```toml
[project.entry-points."format_validator.validators"]
bio = "format_validator_bio.validators"
```

The consumer loads all installed plugins once at startup, before it loads mappings that refer to plugin identifiers:

```python
from format_validator.registry import registry

registry.load_plugins()   # names of the loaded plugins, e.g. ["bio"]
```

A plugin that fails to import is logged and skipped. A plugin that registers an identifier or validator class that is already taken raises a `DuplicateRegistrationError` (a `KeyError`). Plugins run in-process as trusted code.

## Installation

### System Requirements
- Python 3.13.5+
- GDAL

### Environment
Dependencies are managed with [uv](https://docs.astral.sh/uv/). To create a virtual environment and install the package with its development dependencies, run from project root:

```sh
uv sync
```
### Tests
```sh
uv run pytest
```