from dataclasses import dataclass

from .validation_mode import ValidationMode
from .file_input import FileInput
from .format import Format


@dataclass(frozen=True)
class ValidationRequest:
    expected_format: Format
    actual_file: FileInput
    mode: ValidationMode