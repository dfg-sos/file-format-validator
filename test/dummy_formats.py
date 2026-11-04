"""Format identifiers for the core tests, since the core defines none.

    test_group (abstract)
    ├── test_base             concrete, refined by test_refined
    │   └── test_refined
    ├── test_other
    └── test_inner (abstract)
        ├── test_other        child of two formats
        └── test_nested
"""
from format_validator import FormatIdentifier

GROUP = FormatIdentifier("test_group", children_ids=["test_base", "test_other", "test_inner"], is_abstract=True)
BASE = FormatIdentifier("test_base", children_ids=["test_refined"])
REFINED = FormatIdentifier("test_refined")
OTHER = FormatIdentifier("test_other")
INNER = FormatIdentifier("test_inner", children_ids=["test_other", "test_nested"], is_abstract=True)
NESTED = FormatIdentifier("test_nested")
