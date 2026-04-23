from enum import Enum

class ValidationMode(Enum):

    STRUCTURAL = "structural"   # file extension and secondary files or other required aspects
    CRS = "crs"                 # crs only
    STRICT = "strict"           # combination / strict policies: file extension, crs, open and shape type if available