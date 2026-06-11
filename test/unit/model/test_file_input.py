import pytest
from pathlib import Path
from eo_format_validator import FileInput,MultiFileInput


@pytest.fixture
def file_input():
    return FileInput(path=Path("test.txt"))

@pytest.fixture
def multi_file_input():
    return MultiFileInput(path=Path("main.txt"), secondary_files={Path("secondary1.txt"), Path("secondary2.txt")})

def test_equality(file_input,multi_file_input):
    assert file_input == FileInput(path=Path("test.txt"))
    assert file_input != FileInput(path=Path("other.txt"))
    assert multi_file_input == MultiFileInput(path=Path("main.txt"), secondary_files={Path("secondary1.txt"), Path("secondary2.txt")})
    assert multi_file_input != MultiFileInput(path=Path("main.txt"), secondary_files={Path("secondary1.txt")})  
    assert multi_file_input != MultiFileInput(path=Path("main.txt"), secondary_files={Path("secondary1.txt"), Path("secondary3.txt")})
    assert multi_file_input != MultiFileInput(path=Path("main.txt"), secondary_files=set())
    assert multi_file_input != file_input
    
def test_files(file_input,multi_file_input):
    assert file_input.files() == {Path("test.txt")}
    assert multi_file_input.files() == {Path("main.txt"), Path("secondary1.txt"), Path("secondary2.txt")}