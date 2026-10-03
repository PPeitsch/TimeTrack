from datetime import datetime
from typing import Dict, List


def calculate_daily_hours(entries: List[Dict[str, str]]) -> float:
    """Calculate total hours worked in a day based on time entries."""
    total_hours: float = 0.0
    for entry in entries:
        if entry["exit"] and entry["entry"]:
            entry_time = datetime.strptime(entry["entry"], "%H:%M")
            exit_time = datetime.strptime(entry["exit"], "%H:%M")
            diff = exit_time - entry_time
            total_hours += diff.total_seconds() / 3600
    return total_hours
