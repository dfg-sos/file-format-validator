import pytest
from unittest.mock import Mock, patch
from eo_format_validator import EOFormatValidator,ValidationRequest,ValidationMode,ValidationResult,Format,FileInput,ValidationRequestBuilder,ValidationResponseHandler


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

@pytest.fixture
def mock_builder():
    """Create mock builder that returns valid ValidationRequest."""
    builder = Mock(ValidationRequestBuilder)

    mock_validation_request = Mock(ValidationRequest)
    builder.build.return_value = mock_validation_request

    return builder


@pytest.fixture
def mock_handler():
    handler = Mock(ValidationResponseHandler)
    return handler

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

@pytest.fixture
def success_validation_result():
    """Create successful ValidationResult."""
    result = ValidationResult(_source="test")
    result.set_success("Validation passed", "SUCCESS")
    return result


@pytest.fixture
def failed_validation_result():
    """Create failed ValidationResult."""
    result = ValidationResult(_source="test")
    result.set_failure("Validation failed", "FAILED")
    return result



# ------------CORE FUNCTIONALITY TESTS---------

@patch('eo_format_validator.EOFormatValidator.registry')
def test_successful_validation(mock_registry, validation_request, mock_successful_validator):
    """Test successful validation workflow."""

    mock_registry.choose_and_instantiate.return_value = mock_successful_validator

    result = EOFormatValidator.validate(validation_request)

    assert result.is_valid
    assert result.get_validated()
    # assert len(result.get_infos()) > 0

    mock_registry.choose_and_instantiate.assert_called_once()
    mock_successful_validator.validate.assert_called_once()


@patch('eo_format_validator.EOFormatValidator.registry')
def test_validation_fails_with_errors(mock_registry, validation_request, mock_failed_validator):
    """Test validation that returns errors."""

    mock_registry.choose_and_instantiate.return_value = mock_failed_validator

    result = EOFormatValidator.validate(validation_request)

    assert not result.is_valid
    assert result.get_validated()
    assert len(result.get_errors()) > 0


@patch('eo_format_validator.EOFormatValidator.registry')
def test_unsupported_format_returns_warning(mock_registry, validation_request):
    """Test handling of unsupported file format."""

    mock_registry.choose_and_instantiate.return_value = None

    result = EOFormatValidator.validate(validation_request)

    assert result.is_valid
    assert len(result.get_warnings()) == 1   # Unsupported file formats are supposed to result in a warning instead of an error
    assert "not supported" in result.get_warnings()[0].get_message().lower()
    assert result.get_warnings()[0].get_code() == "NOT_SUPPORTED"


@patch('eo_format_validator.EOFormatValidator.registry')
def test_exception_during_validation(mock_registry, validation_request):
    """Test handling of exception during validation."""
    mock_validator = Mock()
    mock_validator.validate.side_effect = RuntimeError("Validation crashed")
    mock_registry.choose_and_instantiate.return_value = mock_validator

    result = EOFormatValidator.validate(validation_request)

    assert result.is_valid
    assert len(result.get_warnings()) == 1   # Exceptions during validation are supposed to result in a warning instead of an error
    assert "exception during validation" in result.get_warnings()[0].get_message().lower()
    assert result.get_warnings()[0].get_code() == "NOT_VALIDATED"



# --------PARAMETER PASSING TESTS----------


@patch('eo_format_validator.EOFormatValidator.registry')
def test_correct_parameters_passed_to_validator(mock_registry, validation_request, mock_successful_validator):
    """Test that ValidationRequest parameters are passed correctly."""

    mock_registry.choose_and_instantiate.return_value = mock_successful_validator

    EOFormatValidator.validate(validation_request)

    mock_successful_validator.validate.assert_called_once()
    call_args = mock_successful_validator.validate.call_args[0]

    assert call_args[0] == validation_request.get_file_format()
    assert call_args[1] == validation_request.get_file_input()
    assert call_args[2] == validation_request.get_validation_mode()


@patch('eo_format_validator.EOFormatValidator.registry')
def test_format_identifier_used_for_validator_selection(mock_registry, validation_request, mock_successful_validator):
    """Test that Format is used to choose validator."""

    mock_registry.choose_and_instantiate.return_value = mock_successful_validator

    EOFormatValidator.validate(validation_request)

    mock_registry.choose_and_instantiate.assert_called_once()
    call_args = mock_registry.choose_and_instantiate.call_args[0]
    assert call_args[0] == validation_request.get_file_format()


# --------VALIDATION MODE TEST---------


@pytest.mark.parametrize("mode", [
    ValidationMode.STRUCTURAL,
    ValidationMode.CRS,
    ValidationMode.STRICT,
])
@patch('eo_format_validator.EOFormatValidator.registry')
def test_different_validation_modes(mock_registry, mode, tmp_path, mock_successful_validator):
    """Test that different validation modes are passed to validator."""

    mock_registry.choose_and_instantiate.return_value = mock_successful_validator

    test_file = tmp_path / "test.tif"
    test_file.write_bytes(b"CONTENT")

    request = ValidationRequest(
        _file_format=Format(_identifier="test_format"),
        _file_input=FileInput(_path=test_file),
        _validation_mode=mode
    )

    EOFormatValidator.validate(request)

    call_args = mock_successful_validator.validate.call_args[0]
    assert call_args[2] == mode


@patch('eo_format_validator.EOFormatValidator.validate')
def test_execute_validation_success(mock_validate, mock_builder, mock_handler,
                                    success_validation_result):
    """Test successful validation workflow."""
    mock_validate.return_value = success_validation_result
    result = EOFormatValidator(mock_builder,mock_handler).run()
    assert result.is_valid
    mock_validate.assert_called_once()
    mock_builder.build.assert_called_once()
    mock_handler.handle_success.assert_called_once_with(success_validation_result)


@patch('eo_format_validator.EOFormatValidator.validate')
def test_execute_validation_handles_build_exception(mock_validate, mock_builder,
                                                    mock_handler):
    """Test handling of exception during builder.build()."""
    mock_builder.build.side_effect = RuntimeError("Build failed")

    result = EOFormatValidator(mock_builder, mock_handler).run()

    assert result.is_valid
    mock_handler.handle_exception.assert_called_once()
    mock_validate.validate.assert_not_called()


@patch('eo_format_validator.EOFormatValidator.validate')
def test_execute_validation_handles_validation_exception(mock_validate, mock_builder,
                                                         mock_handler):
    """Test handling of exception during EOValidator.validate()."""
    mock_validate.side_effect = RuntimeError("Validation crashed")

    result = EOFormatValidator(mock_builder, mock_handler).run()

    assert result.is_valid
    mock_handler.handle_exception.assert_called_once()
    mock_validate.assert_called_once()

@patch('eo_format_validator.EOFormatValidator.validate')
def test_execute_validation_builder_handles_invalid_path( mock_validate, mock_handler):
    """Test CWL Utils validation handles build exception."""
    mock_builder = Mock()
    mock_builder.build.side_effect = ValueError("Invalid input")
    result_dict = EOFormatValidator(mock_builder, mock_handler).run()
    mock_handler.handle_failure.assert_called_once()
    mock_validate.assert_not_called()
