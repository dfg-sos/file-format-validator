from pathlib import Path
from typing import List

from eo_format_validator.core.file_input import FileInput


def check_file_and_path_exist(input_file: FileInput) -> bool:

    if input_file is None:
        return False
    #if file FileTypeError

    path = input_file.get_path()
    if path is None: # https://stackoverflow.com/questions/82831/how-do-i-check-whether-a-file-exists-without-exceptions

        # os.access
        return False

    if not path.is_file(): # true if exists and file
        return False
    return True

def check_file_extensions(input_file: FileInput, expected_file_extensions: List[str]) -> bool:
    path = input_file.get_path()
    for expected_file_extension in expected_file_extensions:
        if path.suffix.lower().__eq__(expected_file_extension.lower()):
            return True
    return False