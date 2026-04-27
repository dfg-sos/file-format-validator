from pathlib import Path

from eo_format_validator.model.validation_mode import ValidationMode
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.format import Format
from eo_format_validator.eo_format_validator import EOValidator
from eo_format_validator.utils.loader import load_validators_from_package

if __name__ == '__main__':
    root = Path(__file__).parents[2]
    p = root / Path("data/geo/WSF2019_v1_8_48.tif")
    # REQUIRED imports of validators, triggering registration with validators
    load_validators_from_package("eo_format_validator.validators",False, False)
    file_format = Format("format_4109")#format_4109FormatGeoTIFF
    input_file = FileInput(Path(p))
    validation_request = ValidationRequest(file_format, input_file, ValidationMode.STRICT)
    print(file_format)
    print(EOValidator.validate(validation_request).to_dict(True))