from datetime import date, datetime


def validate_time_format(time_str: str) -> bool:
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def validate_entries(entries: list) -> tuple[bool, str]:
    if not entries:
        return False, "No entries provided"

    for entry in entries:
        if not all(validate_time_format(t) for t in [entry["entry"], entry["exit"]]):
            return False, "Invalid time format"

        entry_time = datetime.strptime(entry["entry"], "%H:%M")
        exit_time = datetime.strptime(entry["exit"], "%H:%M")

        if exit_time <= entry_time:
            return False, "Exit time must be after entry time"

    return True, ""


def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_workday(check_date: date) -> bool:
    return check_date.weekday() < 5
