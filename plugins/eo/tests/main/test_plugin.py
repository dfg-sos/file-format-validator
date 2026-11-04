"""The EO plugin is loaded by the core through its entry point."""
import subprocess
import sys

from format_validator import FileInput, ValidationMode, ValidationRequest, ValidationStatus, supported_formats, validate
from format_validator.registry import registry
from format_validator_eo import eo_formats
from tests.fixtures import geotiff_no_cog_input


def test_importing_the_core_registers_the_plugin():
    # A fresh process, so that test modules importing format_validator_eo directly do not register it.
    code = (
        "from format_validator import FormatIdentifier; "
        "from format_validator.registry import registry; "
        "ids = registry.get_registered_identifiers(); "
        "assert FormatIdentifier.get('GeoTIFF') in ids, ids; "
        "assert FormatIdentifier.get('COG') in ids, ids; "
        "assert len(ids) >= 15, ids"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_abstract_formats_are_supported():
    assert {eo_formats.GIS, eo_formats.RASTER, eo_formats.VECTOR} <= set(supported_formats())


def test_format_without_validator():
    assert eo_formats.CSV not in supported_formats()
    assert registry.get_validator_class(eo_formats.CSV) is None


def test_validate_real_geotiff(geotiff_no_cog_input):
    request = ValidationRequest(eo_formats.GEOTIFF, geotiff_no_cog_input, ValidationMode.METADATA)
    assert validate(request).status == ValidationStatus.SUCCESS
