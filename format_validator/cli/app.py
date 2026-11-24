"""Command line interface: ``format-validator validate`` (or ``python -m format_validator``).

    format-validator validate --mappings DIR --format IRI [--mode MODE] [--secondary PATH]... [--expect KEY=VALUE]... PATH
    format-validator validate --mappings DIR --manifest FILE|-

Formats are given as external IRIs, e.g. ``https://example.org/formats#NetCDF``, translated by the
mapping files in ``--mappings`` (see ``FormatTranslator.from_directory``). A manifest is a JSON object
that names the files to validate::

    {"<name>": {"format": "https://example.org/formats#NetCDF", "path": "/data/file.nc",
                "secondary_paths": [], "expected_metadata": {"crs": "EPSG:4326"}}}

The name of an entry is any label: it identifies the file in the output.

Exit status: 0 if every file is SUCCESS or UNCERTAIN (UNCERTAIN is reported as a warning on stderr),
1 if a file is FAILURE or could not be validated (ERROR, e.g. its format has no mapping), 2 on a usage
or configuration error, in which case nothing is validated.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional, TextIO

from ..model import FileInput, InvalidRequest, MultiFileInput, ValidationMode
from ..translator import FormatTranslator
from ..validator import build_request, validate
from .errors import UsageError
from .manifest import FileSpec, file_specs
from .printer import PROG, Printer, print_report, print_summary, use_color

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2
MAPPINGS_ENV = "FORMAT_VALIDATOR_MAPPINGS"


def validate_file(spec: FileSpec, mode: ValidationMode, translator: FormatTranslator) -> dict[str, Any]:
    """Validate one file. A request that cannot be validated (no mapping for the format, metadata
    keys the format's validator does not support) yields the status ``ERROR``."""
    report: dict[str, Any] = {"name": spec.name, "path": str(spec.path), "format": spec.format_iri, "mode": mode.value}
    format_identifier = translator.to_local(spec.format_iri)
    files = MultiFileInput(spec.path, set(spec.secondary_paths)) if spec.secondary_paths else FileInput(spec.path)
    try:
        if format_identifier is None:
            raise InvalidRequest(f"Format '{spec.format_iri}' has no mapping")
        request = build_request(format_identifier, files, mode, spec.expected_metadata or None)
    except InvalidRequest as exc:
        error = {"message": str(exc), "severity": "error"}
        return report | {"status": "ERROR", "errors": [error], "warnings": [], "infos": []}
    result = validate(request).to_dict()
    return report | {
        "status": result["status"].upper(),
        "errors": result["errors"],
        "warnings": result["warnings"],
        "infos": result["infos"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROG, description="Validate files against formats.")
    parser.add_argument("-v", "--verbose", action="store_true", help="log informational messages")
    commands = parser.add_subparsers(dest="command", required=True)

    sub = commands.add_parser(
        "validate",
        help="validate files against formats given as IRIs",
        description=__doc__.split("\n\n")[1],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit status: 0 SUCCESS or UNCERTAIN (warns), 1 FAILURE or ERROR, 2 usage or configuration error.",
    )
    sub.add_argument("path", nargs="?", type=Path, help="file to validate (the primary file of a multi-file format)")
    sub.add_argument("--format", dest="format_iri", metavar="IRI", help="IRI of the format the file must have")
    sub.add_argument("--secondary", action="append", default=[], type=Path, metavar="PATH",
                     help="another file of a multi-file format (e.g. .shx, .dbf); repeatable")
    sub.add_argument("--expect", action="append", default=[], metavar="KEY=VALUE",
                     help="expected metadata, e.g. crs=EPSG:4326 (metadata and content mode); repeatable")
    sub.add_argument("--manifest", metavar="FILE", help="JSON manifest of the files to validate, '-' for stdin")
    sub.add_argument("--mode", choices=[m.value for m in ValidationMode], default=ValidationMode.METADATA.value,
                     help="basic: file names only; metadata: header and metadata (default); "
                          "content: also every pixel, feature or record")
    sub.add_argument("--mappings", type=Path, metavar="DIR",
                     help=f"directory of the mapping files (*.json); default: ${MAPPINGS_ENV}")
    sub.add_argument("--json", action="store_true", help="print the results as JSON")
    sub.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                     help="color the output: auto (default) on terminals, unless $NO_COLOR is set")
    return parser


def load_translator(mappings: Optional[Path]) -> FormatTranslator:
    """The translator of the mapping files in ``mappings``, else in ``$FORMAT_VALIDATOR_MAPPINGS``."""
    if mappings is None:
        if not os.environ.get(MAPPINGS_ENV):
            raise UsageError(f"give --mappings DIR or set {MAPPINGS_ENV}")
        mappings = Path(os.environ[MAPPINGS_ENV])
    if not mappings.is_dir():
        raise UsageError(f"mappings directory not found: {mappings}")
    try:
        translator = FormatTranslator.from_directory(mappings)
    except (OSError, ValueError) as exc:
        raise UsageError(f"cannot load the mappings in {mappings}: {exc}") from exc
    if not translator.iris():
        raise UsageError(f"no mapping files (*.json) in {mappings}")
    return translator


def run_validate(args: argparse.Namespace, stdin: TextIO, out: Printer, err: Printer) -> int:
    specs = file_specs(args, stdin)
    translator = load_translator(args.mappings)
    mode = ValidationMode(args.mode)
    reports = []
    for spec in specs:
        report = validate_file(spec, mode, translator)
        reports.append(report)
        if not args.json:
            print_report(report, out)
        if report["status"] == "UNCERTAIN":
            err.message("warning", f"{spec.name} ({spec.path}) could not be fully validated")
    if args.json:
        json.dump({"results": reports}, out.stream, indent=2)
        print(file=out.stream)
    elif len(reports) != 1:
        print_summary(reports, mode, out)
    failed = any(r["status"] in ("FAILURE", "ERROR") for r in reports)
    return EXIT_FAILED if failed else EXIT_OK


def main(argv: Optional[list[str]] = None, stdin: TextIO = sys.stdin, out: TextIO = sys.stdout,
         err: TextIO = sys.stderr) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format=f"{PROG}: %(levelname)s: %(name)s: %(message)s",
        stream=err,
    )
    out_printer = Printer(out, use_color(args.color, out))
    err_printer = Printer(err, use_color(args.color, err))
    try:
        return run_validate(args, stdin, out_printer, err_printer)
    except UsageError as exc:
        err_printer.message("error", str(exc))
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
