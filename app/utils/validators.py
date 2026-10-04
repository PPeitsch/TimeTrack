import re
from datetime import date, datetime

from flask_babel import gettext as _


def validate_time_format(time_str: str) -> bool:
    """Validate if a string is in HH:MM format with leading zeros."""
    if not time_str:
        return False

    try:
        # Check the exact format with regex to ensure leading zeros
        if not re.match(r"^[0-2]\d:[0-5]\d$", time_str):
            return False

        # Also verify it's a valid time
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def validate_entries(entries: list) -> tuple[bool, str]:
    """Validate a list of time entries.

    An exit earlier than its entry means the range ends the next day. Only the
    range that starts last can do that: any range after it would overlap.
    """
    if not entries:
        return False, _("No entries provided")

    starts = []
    overnight_start = None
    for entry in entries:
        # Check if both entry and exit times are provided
        if not entry.get("entry") or not entry.get("exit"):
            return False, _("Entry and exit times are required")

        # Validate time format
        if not validate_time_format(entry["entry"]) or not validate_time_format(
            entry["exit"]
        ):
            return False, _("Invalid time format (use HH:MM)")

        try:
            entry_time = datetime.strptime(entry["entry"], "%H:%M")
            exit_time = datetime.strptime(entry["exit"], "%H:%M")
        except ValueError:
            return False, _("Invalid time values")

        if exit_time == entry_time:
            return False, _("Exit time must be different from entry time")
        if exit_time < entry_time:
            if overnight_start is not None:
                return False, _("Only one time range can end after midnight")
            overnight_start = entry_time
        starts.append(entry_time)

    if overnight_start is not None and overnight_start < max(starts):
        return False, _("Only the last time range of the day can end after midnight")

    return True, ""


def validate_date(date_str: str) -> bool:
    """Validate if a string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_workday(check_date: date) -> bool:
    """Check if a date is a workday (Monday-Friday)."""
    return check_date.weekday() < 5
