from dataclasses import dataclass

from .validation_mode import ValidationMode
from .file_input import FileInput
from .format import Format


@dataclass
class ValidationRequest:
    _file_format: Format
    _file_input: FileInput
    _validation_mode: ValidationMode

    def get_file_format(self) -> Format:
        return self._file_format

    def get_file_input(self) -> FileInput:
        return self._file_input

    def get_validation_mode(self) -> ValidationMode:
        return self._validation_mode
