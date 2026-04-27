import pytest
from unittest.mock import Mock, patch

from eo_format_validator.eo_format_validator import EOFormatValidator
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.model.format import Format
from eo_format_validator.model.file_input import FileInput
from eo_format_validator.model.validation_mode import ValidationMode
from eo_format_validator.model.validation_result import ValidationResult


# -------FIXTURES---------

@pytest.fixture
def mock_successful_validator():
    """Create a mock validator that returns a successful result."""
    validator = Mock()

    success_result = ValidationResult(_source="test_file.tif")
    success_result.set_success("Validation successful", "SUCCESS")
    validator.validate.return_value = success_result

    return validator


@pytest.fixture
def mock_failed_validator():
    """Create a mock validator that returns an invalid result."""
    validator = Mock()

    failed_result = ValidationResult(_source="test_file.tif")
    failed_result.set_failure("Validation mismatch", "MISMATCH")
    validator.validate.return_value = failed_result

    return validator

#https://docs.pytest.org/en/stable/how-to/tmp_path.html
@pytest.fixture
def validation_request(tmp_path):
    """Create a basic ValidationRequest for testing."""
    # Create temp file
    test_file = tmp_path / "test.tif"
    test_file.write_bytes(b"FAKE_TIF_CONTENT")

    return ValidationRequest(
        _file_format=Format(_identifier="fake_geotiff"),
        _file_input=FileInput(_path=test_file),
        _validation_mode=ValidationMode.STRICT
    )



# ------------CORE FUNCTIONALITY TESTS---------

@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_successful_validation(mock_validators, mock_loader,
                               validation_request, mock_successful_validator):
    """Test successful validation workflow."""

    mock_loader.return_value = None
    mock_validators.choose_and_instantiate.return_value = mock_successful_validator

    result = EOFormatValidator._validate(validation_request)

    assert result.is_valid
    assert result.get_validated()
    assert len(result.get_infos()) > 0

    mock_loader.assert_called_once_with("eo_format_validator.validators", False, False)
    mock_validators.choose_and_instantiate.assert_called_once()
    mock_successful_validator.validate.assert_called_once()


@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_validation_fails_with_errors(mock_validators, mock_loader,
                                      validation_request, mock_failed_validator):
    """Test validation that returns errors."""

    mock_loader.return_value = None
    mock_validators.choose_and_instantiate.return_value = mock_failed_validator

    result = EOFormatValidator._validate(validation_request)

    assert not result.is_valid
    assert result.get_validated()
    assert len(result.get_errors()) > 0


@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_unsupported_format_returns_warning(mock_validators, mock_loader,
                                            validation_request):
    """Test handling of unsupported file format."""

    mock_loader.return_value = None
    mock_validators.choose_and_instantiate.return_value = None

    result = EOFormatValidator._validate(validation_request)

    assert result.is_valid
    assert len(result.get_warnings()) == 1   # Unsupported file formats are supposed to result in a warning instead of an error
    assert "not supported" in result.get_warnings()[0].get_message().lower()
    assert result.get_warnings()[0].get_code() == "NOT_SUPPORTED"


@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_exception_during_validation(mock_validators, mock_loader,
                                     validation_request):
    """Test handling of exception during validation."""

    mock_loader.return_value = None
    mock_validator = Mock()
    mock_validator.validate.side_effect = RuntimeError("Validation crashed")
    mock_validators.choose_and_instantiate.return_value = mock_validator

    result = EOFormatValidator._validate(validation_request)

    assert result.is_valid
    assert len(result.get_warnings()) == 1   # Exceptions during validation are supposed to result in a warning instead of an error
    assert "exception during validation" in result.get_warnings()[0].get_message().lower()
    assert result.get_warnings()[0].get_code() == "NOT_VALIDATED"



# --------PARAMETER PASSING TESTS----------


@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_correct_parameters_passed_to_validator(mock_validators, mock_loader,
                                                validation_request, mock_successful_validator):
    """Test that ValidationRequest parameters are passed correctly."""

    mock_loader.return_value = None
    mock_validators.choose_and_instantiate.return_value = mock_successful_validator

    EOFormatValidator._validate(validation_request)

    mock_successful_validator.validate.assert_called_once()
    call_args = mock_successful_validator.validate.call_args[0]

    assert call_args[0] == validation_request.get_file_format()
    assert call_args[1] == validation_request.get_file_input()
    assert call_args[2] == validation_request.get_validation_mode()


@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_format_identifier_used_for_validator_selection(mock_validators, mock_loader,
                                                        validation_request, mock_successful_validator):
    """Test that Format is used to choose validator."""

    mock_loader.return_value = None
    mock_validators.choose_and_instantiate.return_value = mock_successful_validator

    EOFormatValidator._validate(validation_request)

    mock_validators.choose_and_instantiate.assert_called_once()
    call_args = mock_validators.choose_and_instantiate.call_args[0]
    assert call_args[0] == validation_request.get_file_format()


# --------VALIDATION MODE TEST---------


@pytest.mark.parametrize("mode", [
    ValidationMode.STRUCTURAL,
    ValidationMode.CRS,
    ValidationMode.STRICT,
])
@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_different_validation_modes(mock_validators, mock_loader,
                                    mode, tmp_path, mock_successful_validator):
    """Test that different validation modes are passed to validator."""

    mock_loader.return_value = None
    mock_validators.choose_and_instantiate.return_value = mock_successful_validator

    test_file = tmp_path / "test.tif"
    test_file.write_bytes(b"CONTENT")

    request = ValidationRequest(
        _file_format=Format(_identifier="test_format"),
        _file_input=FileInput(_path=test_file),
        _validation_mode=mode
    )

    EOFormatValidator._validate(request)

    call_args = mock_successful_validator.validate.call_args[0]
    assert call_args[2] == mode



# -------------EDGE CASE TEST---------------

@patch('eo_format_validator.eo_format_validator.load_validators_from_package')
@patch('eo_format_validator.eo_format_validator.validators')
def test_validator_loading_is_called(mock_validators, mock_loader, validation_request):
    """Test that validator loading is triggered."""

    mock_loader.return_value = None
    mock_validators.choose_and_instantiate.return_value = None

    EOFormatValidator._validate(validation_request)

    mock_loader.assert_called_once_with("eo_format_validator.validators", False, False)
