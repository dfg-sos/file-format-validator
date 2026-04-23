#@dataclass(frozen=True) #immutable objects
from dataclasses import field, dataclass
from pathlib import Path
from typing import Dict, Any

@dataclass
class FileInput:
    """
       Represents an input file using the following information:
       - path: Path to file's location (can be a directory)
       - extras: placeholder dict for any additional input information
    """

    _path: Path
    _extras: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):

        if not self._path.exists():
            raise ValueError(f"Input '{self._path}' does not exist.")  # catch at initialization before validate()

        if not self._path.is_file():
            # Requires a file instead of a directory.
            raise ValueError(f"Input '{self._path}' is not a file.")  # catch at initialization before validate()

    def get_path(self) -> Path:
        return self._path

    def get_extras(self) -> dict[str, Any]:
        return self._extras
