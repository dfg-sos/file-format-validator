from dataclasses import dataclass
from typing import Optional
from enum import Enum
from .file_input import FileInput
from .format_identifier import FormatIdentifier
from .errors import UnsupportedMode

class ValidationMode(Enum):
    BASIC = "basic"             # file extension only
    STRUCTURAL = "structural"   # file extension + file(s) exist
    FULL = "full"               # file extension, file(s) exist, crs, open file, (geometry type)

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
        return [ValidationMode.BASIC, ValidationMode.STRUCTURAL, ValidationMode.FULL]