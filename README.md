# EO Format Validator
This package provides a validation tool for EO file formats to examine a file according to a specified format. It relies on (ontology-defined) format identifiers to uniquely reference different file formats. For a supported format, the *EO Format Validator* can decide for certain input file whether it adheres to that format specification. Depending on the selected mode, the file extension is validated and the file is opened to infer the coordinate reference system (CRS) or the geometry type for vector file formats.

| Mode | File Extension | File Open | CRS Validation | Geometry Type Validation|
|---|---|---|---|---|
| `BASIC` | &#10004; | &#10005; | &#10005; | &#10005;
| `STRUCTURAL` | &#10004; | &#10004; | &#10005; | &#10005;
| `CRS` | &#10005; | (&#10004;) | &#10004;| &#10005; |
| `FULL` | &#10004; | &#10004; | &#10004;| (&#10004;)


# Installation

### System Requirements
- Python 3.13.5+
- GDAL

### Environment
It is recommended to work in a virtual environment (venv). To create one and install the packages, run the following commands from project root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```
# Tests
## Unittest
```sh
python -m pip install -e .[test]
python -m pytest
```
## Integration Test
### CWL
Since CWL requires a running ontology to resolve references to file format identifiers a local ontology containing the validated EO file formats must be hosted:
```sh
python3 -m http.server -b localhost -d data/ontology/
```

This will make the _.owl_ definition file available on `http://localhost:8000/edamontology_adapted.org.owl`, which is expected by [cwl integration test](test/cwl/).

To include the ontology in cwl files use:
```
$namespaces:
  edam: http://edamontology.org/
$schemas:
  - http://localhost:8000/edamontology_adapted.org.owl
```