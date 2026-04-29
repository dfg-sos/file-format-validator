from pathlib import Path

from eo_format_validator import EOFormatValidator,ValidationRequest,ValidationMode,Format,FileInput


if __name__ == '__main__':
    root = Path(__file__).parents[1]
    p = root / Path("data/geo/WSF2019_v1_8_48.tif")
    file_format = Format("format_4109")
    input_file = FileInput(Path(p))
    validation_request = ValidationRequest(file_format, input_file, ValidationMode.STRICT)
    print(file_format)
    print(EOFormatValidator.validate(validation_request).to_dict(True))