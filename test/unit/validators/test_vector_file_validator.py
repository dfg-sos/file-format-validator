# import pytest
# from unittest.mock import patch
# from typing import List
# from eo_format_validator import FileInput, Format, ValidationResult,ShapeType, VectorFileValidator


# # -------TEST VALIDATOR-------

# class MockVectorFileValidator(VectorFileValidator):
#     """Concrete implementation for testing abstract VectorFileValidator."""

#     def _get_extensions(self) -> List[str]:
#         return ['.shp', '.gpkg']

#     def _validate_shape_type(self, file_format: Format, file_input: FileInput,
#                              validation_result: ValidationResult) -> ValidationResult:
#         """Mock shape type validation."""
#         validation_result.set_success("Shape type validated", "SHAPE_VALID")
#         return validation_result


# # ----------FIXTURES------------

# @pytest.fixture
# def vector_validator():
#     return MockVectorFileValidator()


# @pytest.fixture
# def test_file(tmp_path):

#     file_path = tmp_path / "test.shp"
#     file_path.write_bytes(b"CONTENT")
#     return file_path


# @pytest.fixture
# def file_input(test_file):
#     return FileInput(_path=test_file)


# @pytest.fixture
# def format_obj():
#     return Format(_identifier="test_format", _expected_crs_epsg=4326, _shape_type=ShapeType.MULTILINESTRING)


# @pytest.fixture
# def validation_result(format_obj):
#     return ValidationResult(_source=format_obj.get_identifier())



# # -----------_validate_strict() TESTS------------

# @patch('eo_format_validator.validators.vector_file_validator.validate_crs_with_fiona')
# @patch('eo_format_validator.validators.vector_file_validator.open_with_fiona')
# def test_validate_strict_calls_all_validations(mock_open, mock_crs, vector_validator,
#                                                format_obj, file_input, validation_result):
#     """Test that _validate_strict calls all validation methods."""

#     def mock_open_side_effect(fmt, fi, vr):
#         vr.set_success("Opened", "OPEN_OK")
#         return vr

#     def mock_crs_side_effect(fmt, fi, vr):
#         vr.set_success("CRS OK", "CRS_OK")
#         return vr

#     mock_open.side_effect = mock_open_side_effect
#     mock_crs.side_effect = mock_crs_side_effect

#     validation_result = vector_validator._validate_strict(format_obj, file_input, validation_result)

#     mock_open.assert_called_once()
#     mock_crs.assert_called_once()

#     assert validation_result.is_valid
#     assert validation_result.get_validated
#     assert len(validation_result.get_infos()) == 4  # extension + open + crs + shape_type


# @patch('eo_format_validator.validators.vector_file_validator.validate_crs_with_fiona')
# @patch('eo_format_validator.validators.vector_file_validator.open_with_fiona')
# def test_validate_strict_fails_if_any_validation_fails(mock_open, mock_crs, vector_validator,
#                                                        format_obj, file_input, validation_result):
#     """Test that _validate_strict fails if any sub-validation fails."""

#     def mock_open_side_effect(fmt, fi, vr):
#         vr.set_success("Opened", "OPEN_OK")
#         return vr

#     def mock_crs_side_effect(fmt, fi, vr):
#         vr.set_failure("CRS mismatch", "CRS_MISMATCH")
#         return vr

#     mock_open.side_effect = mock_open_side_effect
#     mock_crs.side_effect = mock_crs_side_effect

#     validation_result = vector_validator._validate_strict(format_obj, file_input, validation_result)

#     assert not validation_result.is_valid
#     assert validation_result.get_validated
#     assert len(validation_result.get_errors()) >= 1


# @patch('eo_format_validator.validators.vector_file_validator.validate_crs_with_fiona')
# @patch('eo_format_validator.validators.vector_file_validator.open_with_fiona')
# def test_validate_strict_includes_shape_type_validation(mock_open, mock_crs, vector_validator,
#                                                         format_obj, file_input, validation_result):
#     """Test that _validate_strict overrides correctly and includes shape_type validation."""

#     def mock_open_side_effect(fmt, fi, vr):
#         vr.set_success("Opened", "OPEN_OK")
#         return vr

#     def mock_crs_side_effect(fmt, fi, vr):
#         vr.set_success("CRS OK", "CRS_OK")
#         return vr

#     mock_open.side_effect = mock_open_side_effect
#     mock_crs.side_effect = mock_crs_side_effect

#     validation_result = vector_validator._validate_strict(format_obj, file_input, validation_result)

#     assert len(validation_result.get_infos()) == 4
#     codes = [info.get_code() for info in validation_result.get_infos()]
#     assert "SHAPE_VALID" in codes
#     assert validation_result.is_valid
#     assert validation_result.get_validated