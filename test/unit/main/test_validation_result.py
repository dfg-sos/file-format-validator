# import pytest

# from eo_format_validator import ValidationResult,Severity



# # -------------CORE FUNCTIONALITY TESTS--------------

# def test_empty_result_is_valid():
#     """Test that an empty ValidationResult is valid."""
#     result = ValidationResult()

#     assert result.is_valid
#     assert result.is_empty
#     assert not result.get_validated()
#     assert len(result.get_errors()) == 0
#     assert len(result.get_warnings()) == 0
#     assert len(result.get_infos()) == 0


# def test_set_failure_turns_result_invalid():
#     """Test that adding an error using set_failure turns result invalid."""
#     result = ValidationResult()

#     result.set_failure("Test error", code="TEST_ERROR")

#     assert not result.is_valid
#     assert result.get_validated()
#     assert len(result.get_errors()) == 1
#     assert result.get_errors()[0].get_message() == "Test error"
#     assert result.get_errors()[0].get_code() == "TEST_ERROR"


# def test_warning_does_not_make_invalid():
#     """Test that warnings don't invalidate result."""
#     result = ValidationResult()

#     result.add_warning("Test warning", code="TEST_WARN")

#     assert result.is_valid
#     assert not result.get_validated()
#     assert len(result.get_warnings()) == 1
#     assert len(result.get_errors()) == 0


# def test_set_success_marks_validated():
#     """Test that set_success marks result as validated."""
#     result = ValidationResult()

#     result.set_success("Validation passed", code="SUCCESS")

#     assert result.get_validated()
#     assert result.is_valid
#     assert len(result.get_infos()) == 1
#     assert result.get_infos()[0].get_message() == "Validation passed"



# # ----------MERGE FUNCTIONALITY TESTS---------


# def test_merge_combines_errors_and_warnings():
#     """Test that merge combines issues from both results."""
#     result1 = ValidationResult()
#     result1.set_failure("Error 1", "E1")
#     result1.add_warning("Warning 1", "W1")

#     result2 = ValidationResult()
#     result2.set_failure("Error 2", "E2")
#     result2.add_info("Info 2", "I2")

#     merged = result1.merge(result2)

#     assert len(merged.get_errors()) == 2
#     assert len(merged.get_warnings()) == 1
#     assert len(merged.get_infos()) == 1
#     assert not merged.is_valid
#     assert merged.get_validated()


# def test_merge_with_empty_result():
#     """Test merging with empty result."""
#     result1 = ValidationResult()
#     result1.set_success("Success", "S1")

#     result2 = ValidationResult()

#     merged = result1.merge(result2)
#     merged2 = result2.merge(result1)
#     assert merged.is_valid
#     assert len(merged.get_infos()) == 1
#     assert merged2.is_valid
#     assert len(merged2.get_infos()) == 1


# def test_merge_with_none_returns_self():
#     """Test that merging with None returns original result."""
#     result = ValidationResult()
#     result.set_success("Success", "S1")

#     merged = result.merge(None)

#     assert merged is result
#     assert merged.is_valid
#     assert len(merged.get_infos()) == 1



# # ---------------FACTORY METHODS TESTS------------

# def test_from_error_creates_invalid_result():
#     """Test from_error factory method."""
#     result = ValidationResult.from_error(
#         source="test.tif",
#         message="File not found",
#         code="NOT_FOUND"
#     )

#     assert result.get_source() == "test.tif"
#     assert not result.is_valid
#     assert result.get_validated()
#     assert len(result.get_errors()) == 1
#     assert result.get_errors()[0].get_message() == "File not found"
#     assert result.get_errors()[0].get_code() == "NOT_FOUND"


# def test_from_exception_creates_result_from_exception():
#     """Test from_exception factory method."""
#     exc = ValueError("Error1")

#     result = ValidationResult.from_exception(
#         source="test.shp",
#         exc=exc,
#         code="ERROR"
#     )

#     assert result.get_source() == "test.shp"
#     assert not result.is_valid
#     assert len(result.get_errors()) == 1
#     assert "Error1" in result.get_errors()[0].get_message()
#     assert result.get_errors()[0].get_code() == "ERROR"



# # ------------SERIALIZATION TESTS------------

# def test_to_dict_serialization():
#     """Test to_dict creates correct dictionary."""
#     result = ValidationResult(_source="test.tif")
#     result.set_failure("Error message", "ERROR_CODE")
#     result.add_warning("Warning message", "WARN_CODE")

#     result_dict = result.to_dict()

#     assert result_dict["source"] == "test.tif"
#     assert result_dict["validated"] is True
#     assert result_dict["summary"]["errors"] == 1
#     assert result_dict["summary"]["warnings"] == 1
#     assert len(result_dict["errors"]) == 1
#     assert len(result_dict["warnings"]) == 1


# def test_to_json_creates_valid_json():
#     """Test to_json creates valid JSON string."""
#     result = ValidationResult(_source="test.gpkg")
#     result.set_success("Success", "SUCCESS")

#     json_str = result.to_json()

#     assert isinstance(json_str, str)
#     assert "test.gpkg" in json_str
#     assert "Success" in json_str

#     import json
#     parsed = json.loads(json_str)
#     assert parsed["source"] == "test.gpkg"


# # --------SUMMARY TESTS-----------

# def test_summary_counts_issues_correctly():
#     """Test that summary property counts issues correctly."""
#     result = ValidationResult()
#     result.set_failure("E1", "ERR1")
#     result.set_failure("E2", "ERR2")
#     result.add_warning("W1", "WARN1")
#     result.add_info("I1", "INFO1")

#     summary = result.summary

#     assert summary["errors"] == 2
#     assert summary["warnings"] == 1
#     assert summary["infos"] == 1


# # -----------ISSUE TYPES TESTS----------

# @pytest.mark.parametrize("add_method,severity,list_attr,affects_validity", [
#     ("set_failure", Severity.ERROR, "get_errors", True),
#     ("add_warning", Severity.WARNING, "get_warnings", False),
#     ("add_info", Severity.INFO, "get_infos", False),
# ])

# def test_different_issue_types(add_method, severity, list_attr, affects_validity):
#     """Test that different issue types are handled correctly."""
#     result = ValidationResult()

#     # Add issue using the appropriate method
#     method = getattr(result, add_method)
#     method("Test message", "TEST_CODE")

#     # Check it was added to correct list
#     issue_list = getattr(result, list_attr)()
#     assert len(issue_list) == 1
#     assert issue_list[0].get_message() == "Test message"
#     assert issue_list[0].get_severity() == severity

#     if affects_validity:
#         assert not result.is_valid
#     else:
#         assert result.is_valid


# # ------EDGE CASES TESTS------

# def test_multiple_errors_accumulate():
#     """Test that multiple errors are accumulated."""
#     result = ValidationResult()

#     result.set_failure("Error 1", "E1")
#     result.set_failure("Error 2", "E2")
#     result.set_failure("Error 3", "E3")

#     assert len(result.get_errors()) == 3
#     assert not result.is_valid


# def test_details_are_preserved():
#     """Test that details dictionary is preserved."""
#     result = ValidationResult()
#     result._details = {"key": "value", "count": 42}

#     details = result.get_details()

#     assert details["key"] == "value"
#     assert details["count"] == 42

#     result.set_success("Success", "SUCCESS")

#     assert details["key"] == "value"
#     assert details["count"] == 42


# # --------INTEGRATION TEST-----------

# def test_validation_workflow():
#     """Test realistic validation workflow."""

#     result = ValidationResult(_source="example.geojson")

#     result.set_success("Extension is valid", "EXT_OK")

#     result.add_warning("CRS not specified", "CRS_MISSING")

#     result.set_failure("File does not exist", "FILE_NOT_FOUND")

#     assert not result.is_valid
#     assert result.get_validated()
#     assert len(result.get_errors()) == 1
#     assert len(result.get_warnings()) == 1
#     assert len(result.get_infos()) == 1

#     result_dict = result.to_dict()
#     assert result_dict["summary"]["errors"] == 1