import pytest
from unittest.mock import Mock, patch

from eo_format_validator.eo_format_validator import EOFormatValidator,EOFormatValidatorWrapper
from eo_format_validator.model.validation_request_builder import ValidationRequestBuilder
from eo_format_validator.model.validation_response_handler import ValidationResponseHandler
from eo_format_validator.model.validation_request import ValidationRequest
from eo_format_validator.model.validation_result import ValidationResult


# -----------FIXTURES-----------


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


# ----------_execute_validation() TESTS----------

@patch('eo_format_validator.eo_format_validator.EOFormatValidator')
def test_execute_validation_success(mock_eo_validator, mock_builder, mock_handler,
                                    success_validation_result):
    """Test successful validation workflow."""
    mock_eo_validator._validate.return_value = success_validation_result
    result = EOFormatValidator.run(mock_builder, mock_handler)
    assert result.is_valid
    mock_builder.build.assert_called_once()
    mock_handler.handle_success.assert_called_once_with(success_validation_result)


@patch('eo_format_validator.eo_format_validator.EOFormatValidator')
def test_execute_validation_handles_build_exception(mock_eo_validator, mock_builder,
                                                    mock_handler):
    """Test handling of exception during builder.build()."""
    mock_builder.build.side_effect = RuntimeError("Build failed")

    result = EOFormatValidator.run(mock_builder, mock_handler)

    assert result.is_valid
    mock_handler.handle_exception.assert_called_once()
    mock_eo_validator.validate.assert_not_called()


@patch('eo_format_validator.eo_format_validator.EOFormatValidator')
def test_execute_validation_handles_validation_exception(mock_eo_validator, mock_builder,
                                                         mock_handler):
    """Test handling of exception during EOValidator.validate()."""
    mock_eo_validator._validate.side_effect = RuntimeError("Validation crashed")

    result = EOFormatValidator.run(mock_builder, mock_handler)

    assert result.is_valid
    mock_handler.handle_exception.assert_called_once()


# -----------execute_cwl_utils_validation() TESTS-----------

@patch('eo_format_validator.eo_format_validator.EOFormatValidator._validate')
@patch('eo_format_validator.eo_format_validator.CWLUtilsRequestBuilder')
def test_cwl_utils_validation_success(mock_builder_class, mock_validate, success_validation_result):
    """Test successful CWL Utils validation."""

    mock_builder = Mock()
    mock_request = Mock(spec=ValidationRequest)
    mock_builder.build.return_value = mock_request
    mock_builder_class.return_value = mock_builder

    mock_validate.return_value = success_validation_result

    result_dict = EOFormatValidatorWrapper.cwl_validation(
        location="/path/to/file.tif",
        secondary_files=[],
        input_format="format_geotiff",
        config={}
    )

    assert isinstance(result_dict, dict)
    assert result_dict["summary"]["errors"] == 0
    mock_validate.assert_called_once_with(mock_request)


@patch('eo_format_validator.eo_format_validator.EOFormatValidator._validate')
@patch('eo_format_validator.eo_format_validator.CWLUtilsRequestBuilder')
def test_cwl_utils_validation_handles_invalid_path(mock_builder_class, mock_validate):
    """Test CWL Utils validation handles build exception."""
    mock_builder = Mock()
    mock_builder.build.side_effect = ValueError("Invalid input")
    mock_builder_class.return_value = mock_builder

    result_dict = EOFormatValidatorWrapper.cwl_validation(
        location="/invalid/path",
        secondary_files=[],
        input_format="format_unknown",
        config=None
    )

    assert isinstance(result_dict, dict)
    assert result_dict["summary"]["errors"] == 1

    errors = result_dict["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == "PATH_ERROR"

    mock_validate.assert_not_called()


@patch('eo_format_validator.eo_format_validator.EOFormatValidator._validate')
@patch('eo_format_validator.eo_format_validator.CWLUtilsRequestBuilder')
def test_cwl_utils_validation_handles_validation_exception(mock_builder_class, mock_validate):
    """Test CWL Utils validation handles validation exception."""
    mock_builder = Mock()
    mock_request = Mock(spec=ValidationRequest)
    mock_builder.build.return_value = mock_request
    mock_builder_class.return_value = mock_builder

    mock_validate.side_effect = RuntimeError("Validation error")

    result_dict = EOFormatValidatorWrapper.cwl_validation(
        location="/path/to/file.tif",
        secondary_files=[],
        input_format="format_geotiff"
    )

    assert isinstance(result_dict, dict)
    assert result_dict["summary"]["warnings"] == 1

    warnings = result_dict["warnings"]
    assert warnings[0]["code"] == "VALIDATION_ERROR"


@patch('eo_format_validator.eo_format_validator.EOFormatValidator._validate')
@patch('eo_format_validator.eo_format_validator.CWLUtilsRequestBuilder')
def test_cwl_utils_validation_with_secondary_files(mock_builder_class, mock_validate,
                                                   success_validation_result):
    """Test CWL Utils validation with secondary files."""
    mock_builder = Mock()
    mock_request = Mock(spec=ValidationRequest)
    mock_builder.build.return_value = mock_request
    mock_builder_class.return_value = mock_builder

    mock_validate.return_value = success_validation_result

    secondary_files = ["/path/file.shx", "/path/file.dbf", "/path/file.prj"]
    result_dict = EOFormatValidatorWrapper.cwl_validation(
        location="/path/file.shp",
        secondary_files=secondary_files,
        input_format="format_shapefile",
        config={"strict": True}
    )

    assert isinstance(result_dict, dict)

    mock_builder_class.assert_called_once_with(
        "/path/file.shp",
        secondary_files,
        "format_shapefile",
        {"strict": True}
    )
    mock_validate.assert_called_once_with(mock_request)
