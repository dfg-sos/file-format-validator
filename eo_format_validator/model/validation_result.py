import json
import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from .validation_request import ValidationRequest

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Cause(Enum):
    PATH_ERROR = "path_error"
    EXTENSION_MISMATCH = "extension_mismatch"

@dataclass(frozen=True)
class Event:
    message: str 
    severity: Severity
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.now())

@dataclass(frozen=True)
class Info(Event):
    severity: Severity = field(default=Severity.INFO, init=False)

@dataclass(frozen=True)
class Warning(Event):
    severity: Severity = field(default=Severity.WARNING, init=False)
    cause: Optional[Cause] = None

@dataclass(frozen=True)
class Error(Event):
    severity: Severity = field(default=Severity.ERROR, init=False)
    cause: Optional[Cause] = None


class ValidationStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    UNCERTAIN = "uncertain"
    INIT = "init"


@dataclass
class ValidationResult:
    """
    General object for the result of validators.
    A ValidationResult can contain errors, warnings, and infos. These are structured and added as issues.
    Additional information can be provided as details.
    """

    _request: ValidationRequest
    _status: ValidationStatus = ValidationStatus.INIT
    _events: List[Event] = field(default_factory=list)  # list of events (errors/warnings/infos) that occurred during validation

    # Getters and setters

    @property
    def status(self) -> ValidationStatus:
        return self._status
    
    @status.setter
    def status(self, value: ValidationStatus):
        if self.status == ValidationStatus.FAILURE or len(self.errors()) > 0:
            self.status = ValidationStatus.FAILURE # Failure overrides success or uncertainty
            return
        self._status = value

    @property
    def request(self) -> ValidationRequest:
        return self._request
    
    @property
    def events(self) -> List[Event]:
        return self._events

    def get(self, severity: Severity) -> List[Event]:
        return [e for e in self._events if e.severity == severity]

    def errors(self):
        return self.get(Severity.ERROR)

    def warnings(self):
        return self.get(Severity.WARNING)

    def infos(self):
        return self.get(Severity.INFO)
    
    # Modifiers
    
    def add(self, event: Event) -> None:
        self._events.append(event)

    def set_success(self, info: Info | None = None) -> 'ValidationResult':
        self.status = ValidationStatus.SUCCESS
        if info:
            self.add(info)
        return self

    def set_failure(self, error: Error) -> 'ValidationResult':
        self.status = ValidationStatus.FAILURE
        self.add(error)
        return self

    def set_uncertainty(self, warning: Warning) -> 'ValidationResult':
        self.status = ValidationStatus.UNCERTAIN
        self.add(warning)
        return self



    # @classmethod
    # def from_error(cls, source: Optional[str], message: str, code: Optional[str] = None, details: Optional[Dict[str,Any]] = None):
    #     vr = cls(_source=source)
    #     vr.set_failure(message, code=code, details=details)
    #     return vr

    # @classmethod
    # def from_exception(cls, source: Optional[str], exc: Exception, code: str = "EXCEPTION", details: Optional[Dict[str,Any]] = None):
    #     return cls.from_error(source, str(exc), code=code, details=details)
    
    # Factories

    @staticmethod
    def success(request: ValidationRequest, event: Info | None) -> 'ValidationResult':
        vr = ValidationResult(_request=request)
        vr.set_success(event)
        return vr
    
    @staticmethod
    def failure(request: ValidationRequest, event: Error) -> 'ValidationResult':
        vr = ValidationResult(_request=request)
        vr.set_failure(event)
        return vr


    # Derived properties



    # @property
    # def is_empty(self) -> bool:
    #     return len(self._events) == 0

    @property
    def summary(self) -> Dict[str,int]:
        return {"errors": len(self.errors()), "warnings": len(self.warnings()), "infos": len(self.infos())}

    # @property
    # def get_report(self):
    #     return {
    #         self._source,
    #         {self._validated},
    #         self.summary,
    #         self._errors,
    #         self._warnings,
    #         self._infos
    #     }

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

    def merge(self, other: 'ValidationResult') -> "ValidationResult":
        if other is None:
            return self
        if not self.request == other.request:
            raise ValueError(f"Cannot merge ValidationResults from different requests: '{self.request}' vs '{other.request}'")
        match other.status:
            case ValidationStatus.FAILURE:
                self.status = ValidationStatus.FAILURE
            case ValidationStatus.UNCERTAIN:
                self.status = ValidationStatus.UNCERTAIN
            case _: pass
        for new_event in [e for e in other.events if e not in self._events]:
            self.add(new_event)
        return self

    def __add__(self, other: 'ValidationResult') -> 'ValidationResult':
        return self.merge(other)
    
    def __bool__(self) -> bool:
        return self.status == ValidationStatus.SUCCESS