from datetime import date, datetime


def validate_time_format(time_str: str) -> bool:
    """Validate if a string is in HH:MM format."""
    if not time_str:
        return False

    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def validate_entries(entries: list) -> tuple[bool, str]:
    """Validate a list of time entries."""
    if not entries:
        return False, "No entries provided"

    for entry in entries:
        # Check if both entry and exit times are provided
        if not entry.get("entry") or not entry.get("exit"):
            return False, "Entry and exit times are required"

        # Validate time format
        if not validate_time_format(entry["entry"]) or not validate_time_format(
            entry["exit"]
        ):
            return False, "Invalid time format (use HH:MM)"

        try:
            entry_time = datetime.strptime(entry["entry"], "%H:%M")
            exit_time = datetime.strptime(entry["exit"], "%H:%M")

            if exit_time <= entry_time:
                return False, "Exit time must be after entry time"
        except ValueError:
            return False, "Invalid time values"

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
