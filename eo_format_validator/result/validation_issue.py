import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from eo_format_validator.result.issue_severity import Severity


@dataclass
class Issue:
    """Represents a single issue (error/warning/info)."""
    _message: str
    _severity: Severity = Severity.ERROR
    _code: Optional[str] = None            # machine interpretable error code
    _path: Optional[str] = None            # JSON path / Feature ID / field name
    _details: Dict[str, Any] = field(default_factory=dict)
    _timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:

        return {
            "message": self._message,
            "severity": self._severity.value,
            "code": self._code,
            "path": self._path,
            "details": self._details,
            "timestamp": self._timestamp,
        }

    def get_message(self) -> str:
        return self._message

    def get_severity(self) -> Severity:
        return self._severity

    def get_code(self) -> Optional[str]:
        return self._code

    def get_path(self) -> Optional[str]:
        return self._path

    def get_details(self) -> Dict[str, Any]:
        return self._details

    def get_timestamp(self) -> str:
        return self._timestamp