"""The command line interface with the EO validators, on real files. Usage and manifests are tested in the core."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

DATA = Path(__file__).parent.parent / "data"
MAPPINGS = DATA / "mappings"
EO = "https://dfg-sos.github.io/ontologies/eo-formats#"


def run(*argv: str, stdin: str = "") -> tuple[int, list[dict], str]:
    """Run ``python -m format_validator validate --json`` in a subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "format_validator", "validate", "--mappings", str(MAPPINGS), "--json", *argv],
        input=stdin, capture_output=True, text=True,
    )
    results = json.loads(result.stdout)["results"] if result.stdout else []
    return result.returncode, results, result.stderr


def test_geojson():
    code, results, _ = run("--format", f"{EO}GeoJSON", str(DATA / "geojson_de.json"))
    assert (code, results[0]["status"]) == (0, "SUCCESS")


def test_expected_crs_mismatch_fails():
    code, results, _ = run("--format", f"{EO}GeoJSON", "--expect", "crs=EPSG:3857", str(DATA / "geojson_de.json"))
    assert (code, results[0]["status"]) == (1, "FAILURE")


def test_geotiff_is_no_shapefile():
    code, results, _ = run("--format", f"{EO}Shapefile", str(DATA / "o41078a2.tif"))
    assert (code, results[0]["status"]) == (1, "FAILURE")


def test_shapefile_with_secondary_files():
    shp = DATA / "gis_osm_buildings_a_free_1.shp"
    secondary = [a for ext in (".shx", ".dbf", ".prj", ".cpg") for a in ("--secondary", str(shp.with_suffix(ext)))]
    code, results, _ = run("--format", f"{EO}Shapefile", *secondary, str(shp))
    assert (code, results[0]["status"]) == (0, "SUCCESS")


@pytest.mark.parametrize("mode", ["basic", "metadata", "content"])
def test_manifest_in_every_mode(mode):
    manifest = json.dumps({
        "vector": {"format": f"{EO}GeoJSON", "path": str(DATA / "geojson_de.json")},
        "raster": {"format": f"{EO}GeoTIFF", "path": str(DATA / "o41078a2.tif")},
    })
    code, results, _ = run("--mode", mode, "--manifest", "-", stdin=manifest)
    assert code == 0
    assert [(r["name"], r["status"], r["mode"]) for r in results] == [
        ("vector", "SUCCESS", mode), ("raster", "SUCCESS", mode),
    ]
