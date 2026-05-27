#@dataclass(frozen=True) #immutable objects
from dataclasses import field, dataclass
from pathlib import Path
from typing import List,Set

@dataclass(frozen=True)
class FileInput:
    """
       Represents an input file using the following information:
       - path: Path to file's location (can be a directory)
       - extras: placeholder dict for any additional input information
    """

    path: Path

    # def __post_init__(self):

    #     if not self.path.exists():
    #         raise ValueError(f"Input '{self.path}' does not exist.")

    #     if not self.path.is_file():
    #         # Requires a file instead of a directory.
    #         raise ValueError(f"Input '{self.path}' is not a file.") 

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

    # def __post_init__(self):

    #     for path in self.secondary_files: # loop files and check existence
    #         if not path.exists():
    #             raise ValueError(f"Input '{path}' does not exist.")  # catch at initialization before validate()

    #         if not path.is_file():
    #             # requires a file instead of a directory.
    #             raise ValueError(f"Input '{path}' is not a file.")  # catch at initialization before validate()


    def files(self):
        return super().files().union(self.secondary_files)

