#@dataclass(frozen=True) #immutable objects
from dataclasses import field, dataclass
from pathlib import Path
from typing import Set

@dataclass(frozen=True)
class FileInput:
    """
       Represents an input file using the following information:
       - path: Path to file's location (can be a directory)
       - extras: placeholder dict for any additional input information
    """

    path: Path

    def files(self) -> Set[Path]:
        return {self.path}
    
    def __eq__(self,other):
        if not isinstance(other, FileInput):
            return False
        return self.files() == other.files()
    
@dataclass(frozen=True)
class MultiFileInput(FileInput):
    """
       Represents an input file consisting of multiple files using the following information:
       - path: Path to file's location (can be a directory)
       - secondary files: field for secondary files (for multi-file formats like Shapefile)
    """

    secondary_files: Set[Path]

    def files(self):
        return super().files().union(self.secondary_files)

