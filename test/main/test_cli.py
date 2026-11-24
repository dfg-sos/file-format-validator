"""Tests for the command line interface, with dummy validators. Real files are tested in the EO plugin."""
import io
import json
import subprocess
import sys

import pytest

from format_validator import cli
from format_validator.cli.printer import short_format
from format_validator.model import FileFormatValidator, ValidationResult
from format_validator.registry import _Registry
from test.dummy_formats import BASE, OTHER

NS = "https://example.org/formats#"
BASE_IRI, OTHER_IRI = f"{NS}Base", f"{NS}Other_Format"


class DummyValidator(FileFormatValidator):
    def get_extensions(self):
        return [".dummy"]

    def assert_can_open(self, request):
        return ValidationResult.success(request)


class BrokenValidator(DummyValidator):
    def assert_can_open(self, request):
        raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def registry(monkeypatch):
    """BASE validated by DummyValidator, OTHER by BrokenValidator (UNCERTAIN)."""
    fresh = _Registry()
    fresh.register(BASE)(DummyValidator)
    fresh.register(OTHER)(BrokenValidator)
    monkeypatch.setattr("format_validator.validator.registry", fresh)
    return fresh


@pytest.fixture
def mappings(tmp_path):
    directory = tmp_path / "mappings"
    directory.mkdir()
    (directory / "example.json").write_text(
        json.dumps({"ontology_uri": NS, "mappings": {"Base": "test_base", "Other_Format": "test_other"}})
    )
    return directory


@pytest.fixture
def dummy(tmp_path):
    path = tmp_path / "file.dummy"
    path.write_text("x")
    return path


def run(mappings, *argv, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(["validate", "--mappings", str(mappings), *argv], io.StringIO(stdin), out, err)
    return code, out.getvalue(), err.getvalue()


def run_json(mappings, *argv, stdin=""):
    code, out, _ = run(mappings, "--json", *argv, stdin=stdin)
    return code, json.loads(out)["results"]


class TestSingleFile:
    def test_success(self, mappings, dummy):
        code, out, err = run(mappings, "--format", BASE_IRI, str(dummy))
        assert code == cli.EXIT_OK
        assert out == f"format-validator: SUCCESS   {dummy} as Base\n"
        assert err == ""

    def test_json(self, mappings, dummy):
        code, results = run_json(mappings, "--format", BASE_IRI, str(dummy))
        assert code == cli.EXIT_OK
        report = results[0]
        assert {k: report[k] for k in ("name", "path", "format", "mode", "status")} == {
            "name": "file.dummy", "path": str(dummy), "format": BASE_IRI, "mode": "metadata", "status": "SUCCESS",
        }
        assert report["errors"] == report["warnings"] == []
        assert isinstance(report["infos"], list)

    def test_wrong_extension_fails(self, mappings, tmp_path):
        code, results = run_json(mappings, "--mode", "basic", "--format", BASE_IRI, str(tmp_path / "file.txt"))
        assert (code, results[0]["status"]) == (cli.EXIT_FAILED, "FAILURE")

    def test_uncertain_passes_with_a_warning(self, mappings, dummy):
        code, out, err = run(mappings, "--format", OTHER_IRI, str(dummy))
        assert code == cli.EXIT_OK
        assert "UNCERTAIN" in out
        assert "warning" in err and "file.dummy" in err

    def test_unmapped_format_is_an_error(self, mappings, dummy):
        code, results = run_json(mappings, "--format", f"{NS}Nope", str(dummy))
        assert (code, results[0]["status"]) == (cli.EXIT_FAILED, "ERROR")
        assert "has no mapping" in results[0]["errors"][0]["message"]

    def test_unsupported_metadata_key_is_an_error(self, mappings, dummy):
        code, results = run_json(mappings, "--format", BASE_IRI, "--expect", "colour=red", str(dummy))
        assert (code, results[0]["status"]) == (cli.EXIT_FAILED, "ERROR")


class TestManifest:
    def test_every_file_is_reported_by_name(self, mappings, dummy):
        manifest = json.dumps({"A": {"format": BASE_IRI, "path": str(dummy)}, "B": {"format": OTHER_IRI, "path": str(dummy)}})
        code, results = run_json(mappings, "--manifest", "-", stdin=manifest)
        assert code == cli.EXIT_OK
        assert [(r["name"], r["status"]) for r in results] == [("A", "SUCCESS"), ("B", "UNCERTAIN")]

    def test_one_failure_fails_but_every_file_is_validated(self, mappings, dummy):
        manifest = json.dumps({"bad": {"format": f"{NS}Nope", "path": str(dummy)}, "good": {"format": BASE_IRI, "path": str(dummy)}})
        code, results = run_json(mappings, "--manifest", "-", stdin=manifest)
        assert code == cli.EXIT_FAILED
        assert [r["status"] for r in results] == ["ERROR", "SUCCESS"]

    def test_from_file(self, mappings, dummy, tmp_path):
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps({"A": {"format": BASE_IRI, "path": str(dummy)}}))
        assert run_json(mappings, "--manifest", str(path))[0] == cli.EXIT_OK

    def test_empty_manifest_validates_nothing(self, mappings):
        assert run_json(mappings, "--manifest", "-", stdin=" \n") == (cli.EXIT_OK, [])

    @pytest.mark.parametrize(
        "manifest",
        [
            "not json",
            "[]",
            '{"A": "x"}',
            json.dumps({"A": {"path": "/x.dummy"}}),
            json.dumps({"A": {"FORMAT": BASE_IRI, "PATH": "/x.dummy"}}),
            json.dumps({"A": {"format": BASE_IRI, "path": "/x", "colour": "red"}}),
            json.dumps({"A": {"format": BASE_IRI, "path": "/x", "expected_metadata": {"crs": 4326}}}),
        ],
    )
    def test_invalid_manifest_is_a_usage_error(self, mappings, manifest):
        code, out, err = run(mappings, "--manifest", "-", stdin=manifest)
        assert (code, out) == (cli.EXIT_USAGE, "")
        assert err.startswith("format-validator: error:")


class TestOutput:
    def test_every_line_is_prefixed(self, mappings, dummy):
        manifest = json.dumps({"a": {"format": f"{NS}Nope", "path": str(dummy)}, "b": {"format": BASE_IRI, "path": str(dummy)}})
        _, out, _ = run(mappings, "--manifest", "-", stdin=manifest)
        lines = out.splitlines()
        assert all(line.startswith("format-validator: ") for line in lines)
        assert lines[0] == f"format-validator: ERROR     a ({dummy}) as Nope"
        assert lines[1].startswith("format-validator:   error: Format")
        assert lines[-1] == "format-validator: 2 files validated (metadata mode): 1 SUCCESS, 1 ERROR"

    @pytest.mark.parametrize("iri, short", [
        (f"{NS}Base", "Base"), ("https://example.org/formats/Base", "Base"), ("https://example.org/formats#", "formats"),
        ("urn:x", "urn:x"),
    ])
    def test_short_format(self, iri, short):
        assert short_format(iri) == short

    def test_empty_manifest(self, mappings):
        assert run(mappings, "--manifest", "-", stdin="{}")[1] == "format-validator: no files to validate\n"

    def test_color_always(self, mappings, dummy):
        _, out, _ = run(mappings, "--color", "always", "--format", BASE_IRI, str(dummy))
        assert "\033[1;32mSUCCESS" in out

    @pytest.mark.parametrize("env, color", [({}, False), ({"FORCE_COLOR": "1"}, True), ({"NO_COLOR": "1", "FORCE_COLOR": "1"}, False)])
    def test_color_auto(self, mappings, dummy, monkeypatch, env, color):
        """Not a terminal, so no color unless forced; NO_COLOR wins."""
        for name in ("NO_COLOR", "FORCE_COLOR"):
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        _, out, _ = run(mappings, "--format", BASE_IRI, str(dummy))
        assert ("\033[" in out) is color

    def test_json_is_never_colored(self, mappings, dummy):
        _, out, _ = run(mappings, "--color", "always", "--json", "--format", BASE_IRI, str(dummy))
        assert "\033[" not in out


class TestUsage:
    @pytest.mark.parametrize(
        "argv",
        [
            ["x.dummy"],
            ["--format", BASE_IRI],
            ["--manifest", "-", "--format", BASE_IRI],
            ["--format", BASE_IRI, "--expect", "crs", "x.dummy"],
        ],
    )
    def test_usage_error(self, mappings, argv):
        code, out, err = run(mappings, *argv)
        assert (code, out) == (cli.EXIT_USAGE, "")
        assert err.startswith("format-validator: error:")

    def test_mappings_from_environment(self, mappings, dummy, monkeypatch):
        monkeypatch.setenv(cli.MAPPINGS_ENV, str(mappings))
        argv = ["validate", "--format", BASE_IRI, str(dummy)]
        assert cli.main(argv, io.StringIO(), io.StringIO(), io.StringIO()) == cli.EXIT_OK

    @pytest.mark.parametrize("setup", ["unset", "absent", "empty", "broken"])
    def test_mappings_error(self, tmp_path, dummy, monkeypatch, setup):
        monkeypatch.delenv(cli.MAPPINGS_ENV, raising=False)
        directory = tmp_path / "mappings"
        if setup in ("empty", "broken"):
            directory.mkdir()
        if setup == "broken":
            (directory / "broken.json").write_text("{}")
        argv = ["validate", "--format", BASE_IRI, str(dummy)]
        if setup != "unset":
            argv[1:1] = ["--mappings", str(directory)]
        err = io.StringIO()
        assert cli.main(argv, io.StringIO(), io.StringIO(), err) == cli.EXIT_USAGE
        assert err.getvalue().startswith("format-validator: error:")


def test_python_m_entry_point():
    """``python -m format_validator`` runs the CLI (in a subprocess, so with the installed plugins)."""
    result = subprocess.run([sys.executable, "-m", "format_validator", "validate", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--manifest" in result.stdout
