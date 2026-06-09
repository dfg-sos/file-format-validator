# import pytest
# from unittest.mock import patch

# from eo_format_validator import ValidationRequest,ValidationMode,FileInput,ShapeType,MultiFileInput

# from eo_format_validator.integration.cwl import CWLUtilsRequestBuilder


# # ------------FIXTURES-----------

# @pytest.fixture
# def simple_config():
#     return {}


# @pytest.fixture
# def full_config():
#     """Config with all optional parameters."""
#     return {
#         "crs": 4326,
#         "shape_type": "Polygon",
#         "validation_mode": "STRICT",
#         "extras": {"key": "value"}
#     }


# # ------------BASIC BUILD TESTS------------

# @patch('pathlib.Path.from_uri')
# def test_build_simple_file_without_secondary_files(mock_from_uri, tmp_path):
#     """Test building ValidationRequest for simple file without secondary files."""

#     test_file = tmp_path / "test.tif"
#     test_file.write_bytes(b"CONTENT")

#     mock_from_uri.return_value = test_file

#     builder = CWLUtilsRequestBuilder(
#         location="file:///path/to/test.tif",
#         secondary_files=[],
#         input_format="namespace/format_geotiff",
#         config={}
#     )

#     validation_request = builder.build()

#     assert isinstance(validation_request, ValidationRequest)
#     assert isinstance(validation_request.get_file_input(), FileInput)
#     assert not isinstance(validation_request.get_file_input(), MultiFileInput)
#     assert validation_request.get_file_format().get_identifier() == "format_geotiff"
#     assert validation_request.get_validation_mode() == ValidationMode.STRUCTURAL


# @patch('pathlib.Path.from_uri')
# def test_build_with_secondary_files(mock_from_uri, tmp_path):
#     """Test building ValidationRequest with secondary files (Shapefile)."""

#     main_file = tmp_path / "test.shp"
#     main_file.write_bytes(b"SHP_CONTENT")

#     secondary_files = []
#     for ext in ['.shx', '.dbf', '.prj']:
#         sec_file = tmp_path / f"test{ext}"
#         sec_file.write_bytes(b"CONTENT")
#         secondary_files.append(sec_file)

#     def mock_from_uri_side_effect(uri):
#         if uri.endswith('.shp'):
#             return main_file
#         elif uri.endswith('.shx'):
#             return secondary_files[0]
#         elif uri.endswith('.dbf'):
#             return secondary_files[1]
#         elif uri.endswith('.prj'):
#             return secondary_files[2]
#         return None

#     mock_from_uri.side_effect = mock_from_uri_side_effect

#     builder = CWLUtilsRequestBuilder(
#         location="file:///path/to/test.shp",
#         secondary_files=[
#             "file:///path/to/test.shx",
#             "file:///path/to/test.dbf",
#             "file:///path/to/test.prj"
#         ],
#         input_format="format_shapefile",
#         config={}
#     )

#     validation_request = builder.build()

#     assert isinstance(validation_request, ValidationRequest)
#     assert isinstance(validation_request.get_file_input(), MultiFileInput)
#     secondary = []
#     multi = validation_request.get_file_input()
#     if isinstance(multi, MultiFileInput):
#         secondary = multi.get_secondary_files()
#     assert len(secondary) == 3
#     assert validation_request.get_file_format().get_identifier() == "format_shapefile"


# # ---------CONFIG PARAMETER TESTS-------------

# @patch('pathlib.Path.from_uri')
# def test_build_with_crs_config(mock_from_uri, tmp_path):
#     """Test that CRS from config is set in Format."""

#     test_file = tmp_path / "test.tif"
#     test_file.write_bytes(b"CONTENT")
#     mock_from_uri.return_value = test_file

#     builder = CWLUtilsRequestBuilder(
#         location="file:///test.tif",
#         secondary_files=[],
#         input_format="format_geotiff",
#         config={"crs": 4326}
#     )

#     validation_request = builder.build()

#     assert validation_request.get_file_format().get_expected_crs_epsg() == 4326


# @patch('pathlib.Path.from_uri')
# def test_build_with_shape_type_config(mock_from_uri, tmp_path):
#     """Test that shape_type from config is set in Format."""

#     test_file = tmp_path / "test.shp"
#     test_file.write_bytes(b"CONTENT")
#     mock_from_uri.return_value = test_file

#     builder = CWLUtilsRequestBuilder(
#         location="file:///test.shp",
#         secondary_files=[],
#         input_format="format_shapefile",
#         config={"shape_type": "Polygon"}
#     )

#     validation_request = builder.build()

#     assert validation_request.get_file_format().get_shape_type() == ShapeType.POLYGON


# @patch('pathlib.Path.from_uri')
# def test_build_with_validation_mode_config(mock_from_uri, tmp_path):
#     """Test that validation_mode from config is used."""

#     test_file = tmp_path / "test.tif"
#     test_file.write_bytes(b"CONTENT")
#     mock_from_uri.return_value = test_file

#     builder = CWLUtilsRequestBuilder(
#         location="file:///test.tif",
#         secondary_files=[],
#         input_format="format_geotiff",
#         config={"validation_mode": "STRICT"}
#     )

#     validation_request = builder.build()

#     assert validation_request.get_validation_mode() == ValidationMode.STRICT


# @patch('pathlib.Path.from_uri')
# def test_build_with_extras_config(mock_from_uri, tmp_path):
#     """Test that extras from config are passed to Format."""

#     test_file = tmp_path / "test.tif"
#     test_file.write_bytes(b"CONTENT")
#     mock_from_uri.return_value = test_file

#     extras = {"key": "value", "count": 113}

#     builder = CWLUtilsRequestBuilder(
#         location="file:///test.tif",
#         secondary_files=[],
#         input_format="format_geotiff",
#         config={"extras": extras}
#     )

#     validation_request = builder.build()

#     assert validation_request.get_file_format().get_extras() == extras
#     assert validation_request.get_file_format().get_extras()["key"] == "value"
#     assert validation_request.get_file_format().get_extras()["count"] == 113


# @patch('pathlib.Path.from_uri')
# def test_build_with_full_config(mock_from_uri, tmp_path, full_config):
#     """Test building with all config parameters set."""

#     test_file = tmp_path / "test.shp"
#     test_file.write_bytes(b"CONTENT")
#     mock_from_uri.return_value = test_file

#     builder = CWLUtilsRequestBuilder(
#         location="file:///test.shp",
#         secondary_files=[],
#         input_format="format_shapefile",
#         config=full_config
#     )

#     validation_request = builder.build()

#     assert validation_request.get_file_format().get_expected_crs_epsg() == 4326
#     assert validation_request.get_file_format().get_shape_type() == ShapeType.POLYGON
#     assert validation_request.get_validation_mode() == ValidationMode.STRICT
#     assert validation_request.get_file_format().get_extras() == {"key": "value"}

# # ------------FORMAT EXTRACTION TESTS---------------

# @pytest.mark.parametrize("input_format,expected_format", [
#     ("format_geotiff", "format_geotiff"),
#     ("http://edamontology.org/format_geotiff", "format_geotiff"),
#     ("http://edamontology.org/format_4103", "format_4103"),
#     ("namespace:format_geotiff", "format_geotiff"),
#     ("https://example.com/format_shapefile", "format_shapefile"),
#     ("edam:format_webprotege_012", "format_webprotege_012"),
#     ("FORMAT_UPPERCASE", "FORMAT_UPPERCASE"),  # Case-sensitive
# ])
# @patch('pathlib.Path.from_uri')
# def test_format_extraction_from_various_inputs(mock_from_uri, tmp_path,
#                                                input_format, expected_format):
#     """Test that format is correctly extracted from various input_format strings."""

#     test_file = tmp_path / "test.file"
#     test_file.write_bytes(b"CONTENT")
#     mock_from_uri.return_value = test_file

#     builder = CWLUtilsRequestBuilder(
#         location="file:///test.file",
#         secondary_files=[],
#         input_format=input_format,
#         config={}
#     )

#     validation_request = builder.build()

#     assert validation_request.get_file_format().get_identifier() == expected_format


# # -----------EDGE CASE-----------------

# @patch('pathlib.Path.from_uri')
# def test_build_with_empty_secondary_files_list(mock_from_uri, tmp_path):
#     """Test that empty secondary_files list creates FileInput, not MultiFileInput."""

#     test_file = tmp_path / "test.tif"
#     test_file.write_bytes(b"CONTENT")
#     mock_from_uri.return_value = test_file

#     builder = CWLUtilsRequestBuilder(
#         location="file:///test.tif",
#         secondary_files=[],
#         input_format="format_geotiff",
#         config={}
#     )

#     validation_request = builder.build()

#     assert isinstance(validation_request.get_file_input(), FileInput)
#     assert not isinstance(validation_request.get_file_input(), MultiFileInput)