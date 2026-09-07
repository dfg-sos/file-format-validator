"""Well-known textual representation of geometry"""
from typing import List, Optional
from pyproj import CRS
from shapely import wkt, GeometryType

from ...model import ValidationResult,ValidationRequest,Error,Cause,Warning,FormatIdentifier
from ...registry import registry
from .vector_file_validator import VectorFileValidator


@registry.register(FormatIdentifier.WKT)
class WKTValidator(VectorFileValidator):

    def get_extensions(self) -> List[str]:
        return ['.wkt', '.txt']

    def _read_wkt_geometries(self, path):
        """Read all geometries from a WKT file, handling various formats.
        
        Handles:
        - Regular WKT (single geometry)
        - EWKT (with SRID prefix: SRID=4326;POINT(...))
        - Multi-line WKT files
        - GeoSPARQL/RDF WKT format (with URI prefix)
        
        Returns:
            List of shapely Geometry objects
        """
        geometries = []
        text = path.read_text(encoding="utf-8").strip()
        
        # Handle multi-line WKT files
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            wkt_text = line
            
            # Remove GeoSPARQL / RDF WKT prefix
            if wkt_text.startswith("<"):
                wkt_text = wkt_text.split(">", 1)[1].strip()
            
            # Remove EWKT prefix (SRID=XXXX;)
            if wkt_text.upper().startswith("SRID="):
                wkt_text = wkt_text.split(";", 1)[1]
            
            try:
                geom = wkt.loads(wkt_text)
                if geom is not None and not geom.is_empty:
                    geometries.append(geom)
            except Exception:
                # Skip invalid geometries
                continue
        
        return geometries

    def assert_can_open(self, request: ValidationRequest) -> ValidationResult:
        path = request.actual_file.path
        try:
            geometries = self._read_wkt_geometries(path)
            if not geometries:
                return ValidationResult.failure(
                    request,
                    Error(message="No valid WKT geometries found in file.", cause=Cause.STRUCTURAL_MALFORMED)
                )
            return ValidationResult.success(request)
        except Exception as exc:
            return ValidationResult.failure(
                request,
                Error(message="Invalid WKT geometry.", cause=Cause.STRUCTURAL_MALFORMED)
            )

    def get_crs(self, request: ValidationRequest) -> Optional[CRS]:
        try:
            text = request.actual_file.path.read_text(encoding="utf-8").strip()
            
            # Handle multi-line WKT - use first geometry for CRS
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            first_line = lines[0] if lines else text
            
            # Check for GeoSPARQL / RDF WKT prefix with CRS URI
            if first_line.startswith("<"):
                # Extract CRS from URI format: <http://www.opengis.net/def/crs/EPSG/0/31370>
                uri_end = first_line.find(">")
                if uri_end != -1:
                    uri = first_line[1:uri_end]
                    # Try to extract EPSG code from URI
                    if "EPSG" in uri and "/0/" in uri:
                        epsg_part = uri.split("/0/")[-1]
                        try:
                            epsg = int(epsg_part)
                            return CRS.from_epsg(epsg)
                        except ValueError:
                            pass
                    # Try to use the URI directly
                    try:
                        return CRS.from_user_input(uri)
                    except Exception:
                        pass
            
            # Check for EWKT prefix (SRID=XXXX;)
            if first_line.upper().startswith("SRID="):
                epsg = int(first_line.split(";", 1)[0].split("=")[1])
                return CRS.from_epsg(epsg)
            else:
                # Try to parse CRS from WKT (less common)
                try:
                    return CRS.from_wkt(first_line)
                except Exception:
                    return None
        except Exception:
            return None

    def get_geometry_types(self, request: ValidationRequest) -> List[GeometryType]:
        """Get all geometry types found in the WKT file.
        
        Handles multi-line WKT files and returns all geometry types present.
        
        Args:
            request: The validation request containing the file to analyze
            
        Returns:
            List of GeometryType enum values found in the file
        """
        types = set()
        try:
            geometries = self._read_wkt_geometries(request.actual_file.path)
            for geom in geometries:
                geom_type_str = geom.geom_type
                if geom_type_str:
                    # Convert string to GeometryType enum
                    try:
                        geom_type = GeometryType[geom_type_str.upper()]
                        types.add(geom_type)
                    except KeyError:
                        # Unknown geometry type, skip
                        pass
        except Exception:
            # Return empty list on error - let assert_geometry_type handle it
            pass
        
        return list(types)
