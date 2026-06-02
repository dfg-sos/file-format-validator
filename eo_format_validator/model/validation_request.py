from dataclasses import dataclass
from typing import Optional
from enum import Enum
from .file_input import FileInput
from .format import CoordinateReferenceSystem, GeometryType

class ValidationMode(Enum):
    BASIC = "basic"             # file extension only
    STRUCTURAL = "structural"   # file extension + file(s) exist
    CRS = "crs"                 # coordinate reference system only
    FULL = "full"               # file extension, file(s) exist, crs, open file, (geometry type)

@dataclass(frozen=True)
class ValidationRequest:
    format_identifier: str
    actual_file: FileInput
    mode: ValidationMode

    def __post_init__(self):
        assert self.mode in self.enabled_modes(), f"Validation mode {self.mode} is not enabled for this request type."

    def enabled_modes(self) -> list[ValidationMode]:
        return [ValidationMode.BASIC, ValidationMode.STRUCTURAL, ValidationMode.FULL]

@dataclass(frozen=True)
class EOValidationRequest(ValidationRequest):
    crs: Optional[CoordinateReferenceSystem] = None
    geometry_type: Optional[GeometryType] = None

    def enabled_modes(self) -> list[ValidationMode]:
        return super().enabled_modes() + [ValidationMode.CRS]