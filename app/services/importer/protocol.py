from dataclasses import dataclass
from typing import Any, List, Optional, Protocol


@dataclass
class TimeEntryRecord:
    date: str  # YYYY-MM-DD
    entry_time: Optional[str] = None  # HH:MM
    exit_time: Optional[str] = None  # HH:MM
    observation: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None


@dataclass
class ImportResult:
    records: List[TimeEntryRecord]
    total_records: int
    valid_records: int
    errors: List[str]


class ImporterProtocol(Protocol):
    def parse(self, file_content: Any) -> ImportResult:
        """Parse file content and return import result."""
        ...
