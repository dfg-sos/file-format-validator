# EO Format Validator
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

## Integration
Integrating the format validator into your project can be achieved with the [ValidationRequestBuilder](format_validator/model/validation_request_builder.py) and the [ValidationResponseHandler](format_validator/model/validation_response_handler.py) interfaces. You pass your implementation of those interfaces to the [FormatValidator](format_validator/validator.py), which first creates a [ValidationRequest](format_validator/model/validation_request.py) using your builder, performs the validation and passes the [ValidationResult](format_validator/model/validation_result.py) to your response handler. Converting from your ontology identifiers to the internal identifiers should be done in the request builder utilizing the [FormatTranslator](format_validator/translator.py) with your custom mappings (e.g. [Test Mappings](test/data/mappings/http---edamontology-org.json))

## Installation

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
```sh
python -m pip install -e .[test]
python -m pytest
```