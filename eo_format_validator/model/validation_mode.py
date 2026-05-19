from enum import Enum

class ValidationMode(Enum):
    BASIC = "basic"             # file extension only
    STRUCTURAL = "structural"   # file extension + file(s) exist
    SRS = "srs"                 # spatial reference system only
    FULL = "full"               # file extension, file(s) exist, srs, open file, (geometry type)