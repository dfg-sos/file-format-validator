"""Human-readable output: one line per file, prefixed with the program name and optionally colored."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, TextIO

from ..model import ValidationMode

PROG = "format-validator"

_SGR = {"bold": "1", "dim": "2", "red": "31", "green": "32", "yellow": "33"}
STATUS_STYLES = {
    "SUCCESS": ("bold", "green"),
    "UNCERTAIN": ("bold", "yellow"),
    "FAILURE": ("bold", "red"),
    "ERROR": ("bold", "red"),
}
EVENT_STYLES = {"error": ("bold", "red"), "warning": ("bold", "yellow")}


def use_color(choice: str, stream: TextIO) -> bool:
    """Whether to color ``stream``: ``always``, ``never``, or ``auto``, which honours ``NO_COLOR`` and
    ``FORCE_COLOR`` (https://no-color.org, https://force-color.org) and else colors terminals only."""
    if choice != "auto":
        return choice == "always"
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return os.environ.get("TERM") != "dumb" and stream.isatty()


class Printer:
    """Prints lines prefixed with ``format-validator:``, so they stand out in a shared log,
    colored with ANSI escape codes if enabled."""

    def __init__(self, stream: TextIO, color: bool):
        self.stream, self.color = stream, color

    def style(self, text: str, *styles: str) -> str:
        if not self.color or not styles:
            return text
        return f"\033[{';'.join(_SGR[s] for s in styles)}m{text}\033[0m"

    def line(self, text: str = "") -> None:
        prefix = self.style(f"{PROG}:", "bold")
        for part in text.split("\n"):
            print(f"{prefix} {part}".rstrip(), file=self.stream)

    def message(self, level: str, text: str) -> None:
        """A diagnostic such as ``format-validator: error: …``."""
        self.line(f"{self.style(level + ':', *EVENT_STYLES[level])} {text}")


def short_format(iri: str) -> str:
    """The local name of a format IRI, after its last ``#`` or ``/``, e.g. ``GeoJSON``."""
    return iri.rstrip("#/").replace("#", "/").rsplit("/", 1)[-1] or iri


def print_report(report: dict[str, Any], printer: Printer) -> None:
    """Print one line for the file, followed by its errors and warnings, indented."""
    status = printer.style(f"{report['status']:<9}", *STATUS_STYLES.get(report["status"], ()))
    path = report["path"]
    label = path if Path(path).name == report["name"] else f"{report['name']} {printer.style(f'({path})', 'dim')}"
    printer.line(f"{status} {label} as {printer.style(short_format(report['format']), 'bold')}")
    for kind in ("errors", "warnings"):
        level = kind[:-1]
        for event in report[kind]:
            message = event["message"].strip().replace("\n", "\n" + " " * (len(level) + 4))
            printer.line(f"  {printer.style(level + ':', *EVENT_STYLES[level])} {message}")


def print_summary(reports: list[dict[str, Any]], mode: ValidationMode, printer: Printer) -> None:
    """One line with the number of files per status."""
    if not reports:
        printer.line("no files to validate")
        return
    counts = {status: sum(r["status"] == status for r in reports) for status in STATUS_STYLES}
    parts = [printer.style(f"{n} {status}", *STATUS_STYLES[status]) for status, n in counts.items() if n]
    files = "1 file" if len(reports) == 1 else f"{len(reports)} files"
    printer.line(f"{files} validated ({mode.value} mode): {', '.join(parts)}")
