from dataclasses import dataclass
from typing import Optional
from enum import Enum
from .file_input import FileInput
from .format_identifier import FormatIdentifier
from .errors import UnsupportedMode

class ValidationMode(Enum):
    BASIC = "basic"             # file extension only
    METADATA = "metadata"       # file extension, file(s) exist, open file and read its header: crs, (declared geometry type)
    CONTENT = "content"         # metadata, plus every pixel, feature or record is read

@dataclass(frozen=True)
class ValidationRequest:
    format_identifier: FormatIdentifier
    actual_file: FileInput
    mode: ValidationMode
    metadata: Optional[object] = None

    def __post_init__(self):
        # Subclasses may restrict enabled_modes().
        if self.mode not in self.enabled_modes():
            raise UnsupportedMode(f"Validation mode {self.mode!r} is not enabled for this request type.")

    def enabled_modes(self) -> list[ValidationMode]:
        return [ValidationMode.BASIC, ValidationMode.METADATA, ValidationMode.CONTENT]