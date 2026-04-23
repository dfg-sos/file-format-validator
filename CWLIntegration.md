# TODO
### Installation
- [cwltool](https://github.com/common-workflow-language/cwltool) and dependencies (for best results use pinned versions in [requirements.txt](requirements.txt)), including the `eo_validator` module and the adapted `cwl-utils`(original version from https://github.com/common-workflow-language/cwl-utils) module


## Usage

Use one of the geospatial formats for the definition in your `cwltool` input (cwl file and input file). The format declaration is required in the cwl file only. However, to support the current fallback mechanism using the original format comparison, the job file requires a format declaration as well. Only local file inputs are supported. To start the `cwltool` execution use:

```
cwltool <cwl file> <job file>
```

During the cwltool execution, the file will be automatically checked according to the config parameters defined. To execute validation procedures with different settings, adjust the `config` parameters in the `call_validator()` function in `file_formats.py` in `cwl-utils`. Therefore, the `crs` parameter can handle a coordinate reference system expectation as EPSG code. The `shape_type` parameter uses the WKT representation of the shape types defined in the `eo_validator`.

Furthermore, it features a `cwltool` integration using `cwl-utils` adaptations to include the functionality in `cwltool` runs.

## Development setup

If you want to make changes to `cwl-utils` or the `eo_validator`, it is recommended to install the respective package as editable. Any code changes will then take immediate effect for the next `cwltool` run:

When installed via [requirements.txt](requirements.txt), this is already configured, otherwise use the following commands:

```sh
pip install -e ./cwl-utils
pip install -e ./eo_validator
```

Note that without editable installation `cwltool` might load the online version of `cwl-utils` first. Therefore, `cwl-utils` needs to be installed first or in the editable version. Alternatively, a local `cwl-utils` module can be built. Using a different version specification as in the original version, this module can be distinctively included in `cwltool`.
However, therefore the `cwltool` [requirements.txt] needs to be adapted to define the local version.