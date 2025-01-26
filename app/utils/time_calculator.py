from datetime import datetime, timedelta
from typing import Dict, List

from app.models.models import ScheduleEntry


def calculate_daily_hours(entries: List[Dict[str, str]]) -> float:
    total_hours = 0
    for entry in entries:
        if entry["exit"] and entry["entry"]:
            entry_time = datetime.strptime(entry["entry"], "%H:%M")
            exit_time = datetime.strptime(entry["exit"], "%H:%M")
            diff = exit_time - entry_time
            total_hours += diff.total_seconds() / 3600
    return total_hours


def calculate_weekly_hours(schedule_entries: List[ScheduleEntry]) -> Dict:
    weekly_total = 0
    weekly_required = len([e for e in schedule_entries if e.date.weekday() < 5]) * 8

    for entry in schedule_entries:
        if not entry.absence_code:
            weekly_total += calculate_daily_hours(entry.entries)

    return {
        "total": weekly_total,
        "required": weekly_required,
        "difference": weekly_total - weekly_required,
    }


def calculate_monthly_hours(schedule_entries: List[ScheduleEntry]) -> Dict:
    monthly_total = 0
    monthly_required = (
        len(
            [e for e in schedule_entries if e.date.weekday() < 5 and not e.absence_code]
        )
        * 8
    )

    for entry in schedule_entries:
        if not entry.absence_code:
            monthly_total += calculate_daily_hours(entry.entries)

    return {
        "total": monthly_total,
        "required": monthly_required,
        "difference": monthly_total - monthly_required,
    }
