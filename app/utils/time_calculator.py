from datetime import datetime, timedelta
from typing import Dict, List


def calculate_daily_hours(entries: List[Dict[str, str]]) -> float:
    """Calculate total hours worked in a day based on time entries.

    An exit earlier than its entry ends the next day (a shift that crosses
    midnight); its hours count for the day the shift started.
    """
    total_hours: float = 0.0
    for entry in entries:
        if entry["exit"] and entry["entry"]:
            entry_time = datetime.strptime(entry["entry"], "%H:%M")
            exit_time = datetime.strptime(entry["exit"], "%H:%M")
            diff = exit_time - entry_time
            if diff < timedelta(0):
                diff += timedelta(days=1)
            total_hours += diff.total_seconds() / 3600
    return total_hours


def format_hours(hours: float, signed: bool = False) -> str:
    """Format decimal hours as H:MM (e.g. 7.5 -> "7:30", -0.25 -> "-0:15")."""
    minutes = round(abs(hours) * 60)
    sign = "-" if hours < 0 and minutes else ("+" if signed and minutes else "")
    return f"{sign}{minutes // 60}:{minutes % 60:02d}"
