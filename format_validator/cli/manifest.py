"""The files to validate, named on the command line or in a JSON manifest."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from .errors import UsageError


@dataclass(frozen=True)
class FileSpec:
    """A file to validate, with the IRI of the format it must have."""

    name: str
    format_iri: str
    path: Path
    secondary_paths: tuple[Path, ...] = ()
    expected_metadata: dict[str, str] = field(default_factory=dict)


def parse_expectations(pairs: list[str]) -> dict[str, str]:
    """Parse ``KEY=VALUE`` arguments into expected metadata."""
    expected = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise UsageError(f"--expect takes KEY=VALUE, got {pair!r}")
        expected[key] = value
    return expected


def parse_manifest(text: str) -> list[FileSpec]:
    """Parse a manifest, see ``format_validator.cli.app``. An empty manifest names no files."""
    if not text.strip():
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UsageError(f"manifest is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise UsageError("manifest must be a JSON object of {name: {format, path, ...}}")
    specs = []
    for name, entry in data.items():
        if not isinstance(entry, dict):
            raise UsageError(f"manifest entry {name!r} must be an object")
        missing = {"format", "path"} - entry.keys()
        if missing:
            raise UsageError(f"manifest entry {name!r} lacks {', '.join(sorted(missing))}")
        unknown = entry.keys() - {"format", "path", "secondary_paths", "expected_metadata"}
        if unknown:
            raise UsageError(f"manifest entry {name!r} has unknown keys: {', '.join(sorted(unknown))}")
        expected = entry.get("expected_metadata") or {}
        if not isinstance(expected, dict) or not all(isinstance(v, str) for v in expected.values()):
            raise UsageError(f"expected_metadata of manifest entry {name!r} must be an object of strings")
        specs.append(
            FileSpec(
                name=str(name),
                format_iri=str(entry["format"]),
                path=Path(entry["path"]),
                secondary_paths=tuple(Path(p) for p in entry.get("secondary_paths") or []),
                expected_metadata={str(k): v for k, v in expected.items()},
            )
        )
    return specs


def file_specs(args: argparse.Namespace, stdin: TextIO) -> list[FileSpec]:
    """The files named on the command line or in the manifest."""
    if args.manifest is not None:
        if args.path or args.format_iri or args.secondary or args.expect:
            raise UsageError("--manifest cannot be combined with PATH, --format, --secondary or --expect")
        if args.manifest == "-":
            return parse_manifest(stdin.read())
        try:
            return parse_manifest(Path(args.manifest).read_text(encoding="utf-8"))
        except OSError as exc:
            raise UsageError(f"cannot read manifest: {exc}") from exc
    if args.path is None or args.format_iri is None:
        raise UsageError("give PATH and --format, or --manifest")
    return [
        FileSpec(
            name=args.path.name,
            format_iri=args.format_iri,
            path=args.path,
            secondary_paths=tuple(args.secondary),
            expected_metadata=parse_expectations(args.expect),
        )
    ]
