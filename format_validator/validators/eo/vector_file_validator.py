from abc import ABC
from typing import Optional, List
from pyproj import CRS
from shapely import GeometryType
import fiona
from fiona.errors import DriverError

from .eo_file_format_validator import EOFileFormatValidator, EOMetadata, eo_metadata, geometry_type_from_string
from format_validator.model import ValidationResult, ValidationRequest, Error, Warning, Info, Cause, ValidationMode


# Compatible geometry types: single-part and multi-part types are considered compatible
COMPATIBLE_GEOMETRY_TYPES = {
    GeometryType.POINT: {GeometryType.POINT, GeometryType.MULTIPOINT},
    GeometryType.MULTIPOINT: {GeometryType.POINT, GeometryType.MULTIPOINT},
    GeometryType.LINESTRING: {GeometryType.LINESTRING, GeometryType.MULTILINESTRING},
    GeometryType.MULTILINESTRING: {GeometryType.LINESTRING, GeometryType.MULTILINESTRING},
    GeometryType.POLYGON: {GeometryType.POLYGON, GeometryType.MULTIPOLYGON},
    GeometryType.MULTIPOLYGON: {GeometryType.POLYGON, GeometryType.MULTIPOLYGON},
}


class VectorFileValidator(EOFileFormatValidator, ABC):
    def metadata_keys(self) -> frozenset[str]:
        return super().metadata_keys() | {"geometry_type"}

    def get_geometry_types(self, request: ValidationRequest) -> List[GeometryType]:
        """Get all geometry types found in the file using Fiona.
        
        This default implementation works for any vector format supported by Fiona.
        Subclasses can override this method for formats requiring special handling.
        
        Args:
            request: The validation request containing the file to analyze
            
        Returns:
            A set of GeometryType enum values found in the file.
            Returns an empty list if no geometries are found.
        """
        MAX_FEATURES_TO_INSPECT = 50  # Sample up to first 50 features
        types = set()
        
        try:
            with fiona.open(str(request.actual_file.path)) as ds:
                for feature, _ in zip(ds, range(MAX_FEATURES_TO_INSPECT)):
                    geom = feature.get('geometry')
                    if geom:
                        geom_type_str = geom.get('type')
                        geom_type = geometry_type_from_string(geom_type_str) if geom_type_str else None
                        if geom_type is not None:
                            types.add(geom_type)
        except Exception:
            # Return empty list on error - let assert_geometry_type handle it
            pass
        
        return list(types)

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        try:
            with fiona.open(str(request.actual_file.path)) as fiona_collection:
                return ValidationResult.success(request)
        except DriverError as e:
            return ValidationResult.failure(
                request,
                Error(message=f"Failed to open file '{request.actual_file.path}' with Fiona:\n{str(e)}", cause=Cause.FILE_OPEN_ERROR)
            )
        except Exception as exc:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Unknown exception occurred while opening '{request.actual_file.path}' with Fiona:\n{exc.__class__}:{str(exc)}", cause=Cause.FILE_OPEN_ERROR)
            )

    def get_crs(self, request: ValidationRequest) -> Optional[CRS]:
        try:
            with fiona.open(request.actual_file.path) as fiona_collection:
                crs = fiona_collection.crs
                if crs is None:
                    return None
                # Try to convert Fiona CRS to pyproj CRS
                try:
                    # Fiona CRS object can be converted to pyproj CRS directly
                    return CRS.from_user_input(str(crs))
                except Exception:
                    # Fallback: try to get EPSG code
                    try:
                        epsg_code = crs.to_epsg()
                        return CRS.from_epsg(epsg_code) if epsg_code else None
                    except Exception:
                        return None
        except Exception as e:
            return None

    def assert_geometry_type(self, request: ValidationRequest) -> ValidationResult:
        """Assert that the file contains the expected geometry type.
        
        This method uses get_geometry_types() to retrieve all geometry types from the file
        and compares them against the expected geometry type.
        
        Behavior:
        - If expected type is None: SUCCESS (skip validation)
        - If no geometry types found: UNCERTAIN
        - If expected type matches at least one actual type:
            - Single type found: SUCCESS
            - Multiple types found: SUCCESS + Warning about mixed types
        - If expected type matches none of the actual types: FAILURE
        
        Args:
            request: The validation request containing the expected geometry type
            
        Returns:
            ValidationResult with appropriate status and messages
        """
        expected_geometry_type = eo_metadata(request).geometry_type
        if expected_geometry_type is None:
            return ValidationResult.success(
                request,
                Info(message="No expected geometry type given, skipping geometry type validation.")
            )
        
        try:
            actual_types = self.get_geometry_types(request)
            
            if not actual_types:
                return ValidationResult.uncertain(
                    request,
                    Warning(message="File has no geometry type defined, cannot validate against expected shape type.", cause=Cause.MISSING_METADATA)
                )
            
            # Check if expected type is compatible with any actual type
            compatible_types = COMPATIBLE_GEOMETRY_TYPES.get(expected_geometry_type, {expected_geometry_type})
            if any(actual in compatible_types for actual in actual_types):
                # Expected type found - success
                result = ValidationResult.success(request)
                # If multiple types found, add a warning about mixed geometry
                if len(actual_types) > 1:
                    type_names = [t.name for t in actual_types]
                    result.add(Warning(
                        message=f"File contains mixed geometry types: {type_names}. Expected type '{expected_geometry_type.name}' is present.",
                        cause=Cause.STRUCTURAL_MALFORMED
                    ))
                return result
            
            # Expected type not found - failure
            type_names = [t.name for t in actual_types]
            return ValidationResult.failure(
                request,
                Error(message=f"File geometry types {type_names} do not include expected type '{expected_geometry_type.name}'.", cause=Cause.METADATA_MISMATCH)
            )
        except Exception as e:
            return ValidationResult.uncertain(
                request,
                Warning(message=f"Unexpected error while validating geometry type:\n{str(e)}", cause=Cause.UNKNOWN)
            )

    def validate(self, request: ValidationRequest) -> ValidationResult:
        result = super().validate(request)
        if not isinstance(request.metadata, EOMetadata):
            return result
        match request.mode:
            case ValidationMode.FULL:
                result += self.assert_geometry_type(request)
            case _:
                pass
        return result