from datetime import datetime, timedelta
from typing import Dict, List

from app.models.models import ScheduleEntry


def calculate_daily_hours(entries: List[Dict[str, str]]) -> float:
    """Calculate total hours worked in a day based on time entries."""
    total_hours = 0
    for entry in entries:
        if entry["exit"] and entry["entry"]:
            entry_time = datetime.strptime(entry["entry"], "%H:%M")
            exit_time = datetime.strptime(entry["exit"], "%H:%M")
            diff = exit_time - entry_time
            total_hours += diff.total_seconds() / 3600
    return total_hours


def calculate_weekly_hours(schedule_entries: List[ScheduleEntry]) -> Dict:
    """Calculate weekly hours worked and required."""
    weekly_total = 0
    # Count working days (Monday-Friday) without absence code
    working_days = [
        e for e in schedule_entries if e.date.weekday() < 5 and not e.absence_code
    ]

    # Required hours is 8 hours per working day
    weekly_required = len(working_days) * 8

    # Calculate actual hours worked
    for entry in schedule_entries:
        if not entry.absence_code:
            weekly_total += calculate_daily_hours(entry.entries)

    return {
        "total": weekly_total,
        "required": weekly_required,
        "difference": weekly_total - weekly_required,
    }


def calculate_monthly_hours(schedule_entries: List[ScheduleEntry]) -> Dict:
    """Calculate monthly hours worked and required."""
    monthly_total = 0

    # Count working days (Monday-Friday) without absence code
    working_days = [
        e for e in schedule_entries if e.date.weekday() < 5 and not e.absence_code
    ]

    # Required hours is 8 hours per working day
    monthly_required = len(working_days) * 8

    # Calculate actual hours worked
    for entry in schedule_entries:
        if not entry.absence_code:
            monthly_total += calculate_daily_hours(entry.entries)

    return {
        "total": monthly_total,
        "required": monthly_required,
        "difference": monthly_total - monthly_required,
    }
