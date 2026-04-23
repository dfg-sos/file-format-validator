import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from eo_format_validator.result.issue_severity import Severity
from eo_format_validator.result.validation_issue import Issue


@dataclass #-> automatic __init__
class ValidationResult:
    """
    General object for the result of validators.
    A ValidationResult can contain errors, warnings, and infos. These are structured and added as issues.
    Additional information can be provided as details.
    """

    _source: Optional[str] = ""                    # path or identifier of the tested resource
    _validated: bool = False                       # flag == true if validation took place, regardless of the outcome
    _uncertain: bool = False                       # flag == true if validation could not be performed
    _errors: List[Issue] = field(default_factory=list)
    _warnings: List[Issue] = field(default_factory=list)
    _infos: List[Issue] = field(default_factory=list)
    _details: Dict[str, Any] = field(default_factory=dict)

    # --- convenience / mutators ------------------------------------------------
    def add_issue(self, issue: Issue) -> None:
        if issue.get_severity() == Severity.ERROR:
            self._errors.append(issue)
        elif issue.get_severity() == Severity.WARNING:
            self._warnings.append(issue)
        else:
            self._infos.append(issue)

    def add_warning(self, message: str, code: Optional[str] = None, path: Optional[str] = None, details: Optional[Dict[str,Any]] = None):
        self.add_issue(Issue(_message=message, _severity=Severity.WARNING, _code=code, _path=path, _details=(details or {})))

    def add_info(self, message: str, code: Optional[str] = None, path: Optional[str] = None, details: Optional[Dict[str,Any]] = None):
        self.add_issue(Issue(_message=message, _severity=Severity.INFO, _code=code, _path=path, _details=(details or {})))

    def set_success(self, message: str, code: Optional[str] = None, path: Optional[str] = None, details: Optional[Dict[str,Any]] = None) -> None:
        self.set_validated()
        self.add_info(message, code, path, details)

    def set_failure(self, message: str, code: Optional[str] = None, path: Optional[str] = None, details: Optional[Dict[str,Any]] = None):
        self.set_validated()
        self.add_issue(Issue(_message=message, _severity=Severity.ERROR, _code=code, _path=path, _details=(details or {})))

    def set_uncertainty(self, message: str, code: Optional[str] = None, path: Optional[str] = None, details: Optional[Dict[str,Any]] = None):
        self.set_uncertain()
        self.add_warning(message, code, path, details)

    def get_source(self):
        return self._source

    def get_errors(self):
        return self._errors

    def get_warnings(self):
        return self._warnings

    def get_infos(self):
        return self._infos

    def get_details(self):
        return self._details

    #def set_fallback(self):
    #    self.fallback = True

    def set_validated(self):
        self._validated = True

    def get_validated(self) -> bool:
        return self._validated

    def invalidate(self):
        self._validated = False

    def set_uncertain(self):
        self._uncertain = True

    def get_uncertain(self) -> bool:
        return self._uncertain

    @classmethod
    def from_error(cls, source: Optional[str], message: str, code: Optional[str] = None, details: Optional[Dict[str,Any]] = None):
        vr = cls(_source=source)
        vr.set_failure(message, code=code, details=details)
        return vr

    @classmethod
    def from_exception(cls, source: Optional[str], exc: Exception, code: str = "EXCEPTION", details: Optional[Dict[str,Any]] = None):
        return cls.from_error(source, str(exc), code=code, details=details)

    # --- derived properties ---------------------------------------------------
    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0

    @property
    def is_empty(self) -> bool:
        return not self._validated and len(self._errors) == 0 and len(self._warnings) == 0 and len(self._infos) == 0

    @property
    def summary(self) -> Dict[str,int]:
        return {"errors": len(self._errors), "warnings": len(self._warnings), "infos": len(self._infos)}

    @property
    def get_report(self):
        return {
            self._source,
            {self._validated},
            self.summary,
            self._errors,
            self._warnings,
            self._infos
        }

    # --- utility --------------------------------------------------------------
    def to_dict(self, include_details: bool = True) -> Dict[str, Any]:
        d = {
            "source": self._source,
            "validated": self._validated,
            "summary": self.summary,
            "errors": [i.to_dict() for i in self._errors],
            "warnings": [i.to_dict() for i in self._warnings],
            "infos": [i.to_dict() for i in self._infos],
        }
        if include_details:
            d["details"] = self._details
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

    # merging results
    def merge(self, other: 'ValidationResult') -> "ValidationResult":
        """Merge: errors/warnings/infos + details.
           Two ValidationResults are validated if both are validated separately. Ignore empty ValidationResults.
        """
        if other is None:
            return self
        if not self.is_empty and not other.is_empty:
            self._validated = self._validated and other.get_validated()
        elif not other.is_empty:
            self._validated = other.get_validated()
        # if other is empty remains self.validated, if both are empty, remains False
        if other._source and not self._source:
            self._source = other.get_source()
        #if other.top_type and not self.top_type:
        #    self.top_type = other.top_type
        def extend_unique(first: Optional[List[Issue]], second: Optional[List[Issue]]) -> List[Issue]:
            """
               Extends list of Issues 'first' by all elements in list of Issues 'second' that are not yet included in first.
               - accounts for None and empty lists
               - extends 'first' and returns 'first'
            """
            if not first:
                return second
            if not second:
                return first

            for issue in second:
                if issue not in first:
                    first.append(issue)
            return first

        self._errors = extend_unique(self._errors, other.get_errors())
        self._warnings = extend_unique(self._warnings, other.get_warnings())
        self._infos = extend_unique(self._infos, other.get_infos())
        #self.get_warnings().extend(other.get_warnings())
        #self.get_infos().extend(other.get_infos())
        # shallow merge of details, existing keys preserved
        for k, v in other.get_details().items():
            self._details.setdefault(k, v)
        return self

    #def raise_for_errors(self) -> None:
    #    """Raise Exception if validation failed."""
    #    if not self.is_valid:
    #        msgs = "; ".join([e.get_message() for e in self.get_errors()])
    #        raise ValidationError(f"Validation failed: {msgs}")

    def __str__(self) -> str:
        sb = [f"ValidationResult(source={self._source!r}, valid={self.is_valid}, validated={self._validated})",
              f"  errors={len(self._errors)}, warnings={len(self._warnings)}, infos={len(self._infos)}"]
        if self._details:
            sb.append(f"  details keys={list(self._details.keys())}")
        return "\n".join(sb)