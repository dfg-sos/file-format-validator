#@dataclass(frozen=True) #immutable objects
from dataclasses import field, dataclass
from pathlib import Path
from typing import List

from eo_format_validator.core.file_input import FileInput


@dataclass
class MultiFileInput(FileInput):
    """
       Represents an input file consisting of multiple files using the following information:
       - path: Path to file's location (can be a directory)
       - secondary files: optional field for secondary files (for multi-file formats like Shapefile)
       - extras: placeholder dict for any additional input information
    """

    _secondary_files: List[Path] = field(default_factory=list)

    def __post_init__(self):

        for path in self._secondary_files: # loop files and check existence
            if not path.exists():
                raise ValueError(f"Input '{path}' does not exist.")  # catch at initialization before validate()

            if not path.is_file():
                # requires a file instead of a directory.
                raise ValueError(f"Input '{path}' is not a file.")  # catch at initialization before validate()

    def get_secondary_files(self) -> list[Path]:
        return self._secondary_files
