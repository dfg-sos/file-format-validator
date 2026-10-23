from abc import ABC, abstractmethod
import json
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
from .validation_request import ValidationRequest

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Cause(Enum):
    PATH_ERROR = "path_error"
    EXTENSION_MISMATCH = "extension_mismatch"
    METADATA_MISMATCH = "invalid_metadata"
    MISSING_METADATA = "srs_missing"
    FILE_OPEN_ERROR = "file_open_error"
    STRUCTURAL_MALFORMED = "structural_malformed"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class Event(ABC):
    message: str
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.now())

    @abstractmethod
    def severity(self) -> Severity:
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the event to a dictionary."""
        d = asdict(self)
        d["severity"] = self.severity().value
        d["timestamp"] = self.timestamp.isoformat()
        d.pop("cause", None)
        if hasattr(self, "cause") and self.cause is not None: # type: ignore
            d["cause"] = self.cause.value # type: ignore
        return d

@dataclass(frozen=True)
class Info(Event):
    def severity(self) -> Severity:
        return Severity.INFO

@dataclass(frozen=True)
class Warning(Event):
    cause: Optional[Cause] = None

    def severity(self) -> Severity:
        return Severity.WARNING

@dataclass(frozen=True)
class Error(Event):
    cause: Optional[Cause] = None

    def severity(self) -> Severity:
        return Severity.ERROR


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
        return self._status if self._status != ValidationStatus.INIT else ValidationStatus.SUCCESS
    
    @status.setter
    def status(self, value: ValidationStatus):
        if self._status == ValidationStatus.FAILURE or len(self.errors()) > 0:
            self._status = ValidationStatus.FAILURE # Failure overrides success or uncertainty
            return
        self._status = value

    @property
    def request(self) -> ValidationRequest:
        return self._request
    
    @property
    def events(self) -> List[Event]:
        return self._events

    def get(self, severity: Severity) -> List[Event]:
        return [e for e in self._events if e.severity() == severity]

    def errors(self):
        return self.get(Severity.ERROR)

    def warnings(self):
        return self.get(Severity.WARNING)

    def infos(self):
        return self.get(Severity.INFO)
    
    def add(self, event: Event) -> None:
        self._events.append(event)
        match event.severity():
            case Severity.ERROR:
                self.status = ValidationStatus.FAILURE
            case Severity.WARNING:
                if self._status == ValidationStatus.INIT:
                    self.status = ValidationStatus.UNCERTAIN
            case _: pass

    def set_success(self, info: Info | None = None) -> 'ValidationResult':
        if info:
            self.add(info)
        self.status = ValidationStatus.SUCCESS
        return self

    def set_failure(self, error: Error) -> 'ValidationResult':
        self.add(error)
        return self

    def set_uncertainty(self, warning: Warning) -> 'ValidationResult':
        self.add(warning)
        return self

    # Factories

    @staticmethod
    def success(request: ValidationRequest, event: Info | None = None) -> 'ValidationResult':
        vr = ValidationResult(_request=request)
        vr.set_success(event)
        return vr
    
    @staticmethod
    def failure(request: ValidationRequest, event: Error) -> 'ValidationResult':
        vr = ValidationResult(_request=request)
        vr.set_failure(event)
        return vr
    
    @staticmethod
    def uncertain(request: ValidationRequest, event: Warning) -> 'ValidationResult':
        vr = ValidationResult(_request=request)
        vr.set_uncertainty(event)
        return vr
    

    # --- utility --------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the validation result to a dictionary."""
        return {
            "status": self.status.value,
            "request": {
                "format_identifier": self._request.format_identifier.id,
                "file": str(self._request.actual_file.path),
                "mode": self._request.mode.value,
            },
            "events": [e.to_dict() for e in self._events],
            "errors": [e.to_dict() for e in self.errors()],
            "warnings": [e.to_dict() for e in self.warnings()],
            "infos": [e.to_dict() for e in self.infos()],
        }

    def to_json(self) -> str:
        """Serialize the validation result to a JSON string."""
        return json.dumps(self.to_dict(), indent=4)

    def merge(self, other: 'ValidationResult | None') -> "ValidationResult":
        if other is None:
            return self
        if not self.request == other.request:
            raise ValueError(f"Cannot merge ValidationResults from different requests: '{self.request}' vs '{other.request}'")
        match other.status:
            case ValidationStatus.FAILURE:
                self.status = ValidationStatus.FAILURE
            case ValidationStatus.UNCERTAIN:
                self.status = ValidationStatus.UNCERTAIN
            case _: 
                self.status = self.status
        for new_event in [e for e in other.events if e not in self._events]:
            self.add(new_event)
        return self

    def __add__(self, other: 'ValidationResult') -> 'ValidationResult':
        return self.merge(other)
    
    def __bool__(self) -> bool:
        return self.status == ValidationStatus.SUCCESS