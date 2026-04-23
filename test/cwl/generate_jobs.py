#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any

class Format(Enum):
    COG = "4100"
    GEOJSON = "4106"
    GEOPACKAGE = "4107"
    GEOPARQUET = "4108"
    GEOTIFF = "4109"
    GEOZARR = "4110"
    GRIB = "4113"
    KML = "4114"
    NETCDF = "4115"
    OSM = "4117"
    SHAPEFILE = "4119"
    WKT = "4122"
    GEOSPATIAL = "4124"
    RASTER = "4125"
    VECTOR = "4126"

class TestCase:
    def __init__(self,format:Format, input_data: Path, job_file_suffix: str = "", set_format_in_job_file: bool = False):
        self.format = format
        self.input_data = input_data
        self.set_format_in_job_file = set_format_in_job_file
        self.job_file_suffix = job_file_suffix

    def to_job_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "eo_file": {
                "class": "File",
                "path": self.input_data.as_posix(),
            }
        }
        if self.set_format_in_job_file:
            payload["eo_file"]["format"] = f"edam:format_{self.format.value}"
        return payload


def build_test_cases(data_dir: Path) -> list[TestCase]:
    base_test_cases = [
        TestCase(Format.COG, data_dir / "o41078a2.tif"),
        TestCase(Format.GEOJSON, data_dir / "geojson_de.json"),
        TestCase(Format.GEOPACKAGE, data_dir / "test_raster_only_full.gpkg","raster"),
        TestCase(Format.GEOPACKAGE, data_dir / "Italian_cities.gpkg","vector"),
        TestCase(Format.GEOPARQUET, data_dir / "example.parquet"),
        TestCase(Format.GEOPARQUET, data_dir / "hannover_buildings.geoparquet"),
        TestCase(Format.GEOTIFF, data_dir / "WSF2019_v1_8_48.tif"),
        TestCase(Format.GEOZARR, data_dir / "WSF2019_v1_8_48.tif"),
        TestCase(Format.GRIB, data_dir / "Cyprus_SKIRON_090326.grb"),
        TestCase(Format.KML, data_dir / "KML_Samples.kml"),
        TestCase(Format.NETCDF, data_dir / "sresa1b_ncar_ccsm3-example.nc"),
        TestCase(Format.NETCDF, data_dir / "pr_2018.nc"),
        TestCase(Format.OSM, data_dir / "osm_file_933.osm"),
        TestCase(Format.SHAPEFILE, data_dir / "gis_osm_buildings_a_free_1.shp"),
        TestCase(Format.WKT, data_dir / "wkt_example.wkt"),
    ]
    format_test_cases = [TestCase(test_case.format, test_case.input_data, test_case.job_file_suffix, set_format_in_job_file=True) for test_case in base_test_cases]
    return base_test_cases + format_test_cases


def get_project_root() -> Path:
    """Return project root via PROJECT_ROOT env var or script-relative fallback."""
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    # Script path: <root>/test/cwltool/generate_jobs.py
    return Path(__file__).resolve().parent.parent

def main() -> None:
    DATA_DIR_RELATIVE_PATH = Path("data/geo")
    JOB_DIR = Path(__file__).parent / "jobs"
    JOB_DIR.mkdir(exist_ok=True)
    project_root = get_project_root()
    for test_case in build_test_cases(project_root / DATA_DIR_RELATIVE_PATH):
        job_payload = test_case.to_job_payload()
        job_file_name = f"job_{test_case.format.name.lower()}{"_" + test_case.job_file_suffix if test_case.job_file_suffix else ''}.json"
        if test_case.set_format_in_job_file:
            job_file_name = job_file_name.replace(".json", "_with_format.json")
        with open(JOB_DIR / job_file_name, "w") as f:
            json.dump(job_payload, f, indent=4)

if __name__ == "__main__":
    main()
