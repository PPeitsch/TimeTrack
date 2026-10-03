"""Single source of truth for what kind of day a date is and how many hours it needs.

The calendar, the summary and the time log all go through `resolve_days`, so
they agree on precedence:

1. A day with an absence code is that absence (0 required, 0 worked).
2. Otherwise hours logged on the day always count as worked, even on a weekend
   or holiday (they show up as overtime).
3. Required hours apply only to regular working days: weekdays that are not a
   holiday. An explicit "Work Day" override on a weekend or holiday shows the
   day as a work day but does not add required hours.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Set, cast

from flask import current_app

from app.models.models import Holiday, ScheduleEntry
from app.services.holiday_sync import ensure_holidays
from app.utils.time_calculator import calculate_daily_hours

WORK_DAY = "Work Day"
HOLIDAY = "Holiday"
WEEKEND = "Weekend"


@dataclass
class DayInfo:
    date: date
    type: str
    base_type: str = WORK_DAY  # type from the base calendar, ignoring overrides
    worked: float = 0.0
    required: float = 0.0
    entries: List[Dict[str, str]] = field(default_factory=list)
    absence_code: Optional[str] = None
    observation: Optional[str] = None
    has_entry: bool = False

    @property
    def difference(self) -> float:
        return self.worked - self.required


def hours_per_day() -> float:
    return float(current_app.config.get("WORKING_HOURS_PER_DAY", 8))


def resolve_days(employee_id: int, start: date, end: date) -> List[DayInfo]:
    """Return one DayInfo per date in [start, end] for the given employee."""
    for year in range(start.year, end.year + 1):
        ensure_holidays(year)

    entries = ScheduleEntry.query.filter(
        ScheduleEntry.date.between(start, end),
        ScheduleEntry.employee_id == employee_id,
    ).all()
    entries_map = {entry.date: entry for entry in entries}
    holidays: Set[date] = {
        h.date for h in Holiday.query.filter(Holiday.date.between(start, end)).all()
    }

    days = []
    current = start
    while current <= end:
        days.append(_resolve(current, entries_map.get(current), holidays))
        current += timedelta(days=1)
    return days


def resolve_day(employee_id: int, day: date) -> DayInfo:
    return resolve_days(employee_id, day, day)[0]


def _resolve(day: date, entry: Optional[ScheduleEntry], holidays: Set[date]) -> DayInfo:
    if day in holidays:
        base_type = HOLIDAY
    elif day.weekday() >= 5:
        base_type = WEEKEND
    else:
        base_type = WORK_DAY

    if entry is None:
        required = hours_per_day() if base_type == WORK_DAY else 0.0
        return DayInfo(date=day, type=base_type, base_type=base_type, required=required)

    absence_code = cast(Optional[str], entry.absence_code)
    info = DayInfo(
        date=day,
        type=base_type,
        base_type=base_type,
        absence_code=absence_code,
        observation=cast(Optional[str], entry.observation),
        has_entry=True,
    )
    if absence_code:
        info.type = absence_code
        return info

    # Explicit entry without absence: a work day, possibly an override.
    info.type = WORK_DAY
    info.entries = list(entry.entries or [])
    info.worked = calculate_daily_hours(info.entries)
    info.required = hours_per_day() if base_type == WORK_DAY else 0.0
    return info


def summarize(days: List[DayInfo]) -> Dict[str, float]:
    worked = sum(d.worked for d in days)
    required = sum(d.required for d in days)
    return {"total": worked, "required": required, "difference": worked - required}
