"""Sample data so a fresh install (or the public demo) has something to show.

Generates working days for the last few months: varied entry and exit times, a
lunch break on some days, a vacation week, a sick day and a few observations.
Days that already have an entry are never touched, so running it twice is safe.
"""

import random
from datetime import date, timedelta
from typing import List, Optional, Set

from app.auth import DEFAULT_EMPLOYEE_ID
from app.db.database import db
from app.models.models import Holiday, ScheduleEntry
from app.services.holiday_sync import ensure_holidays

OBSERVATIONS = [
    "Sprint planning",
    "Deploy to production",
    "Dentist in the morning",
    "Worked from home",
    "Team offsite",
]


def _time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _workday(rng: random.Random) -> List[dict]:
    start = rng.choice(range(8 * 60, 9 * 60 + 31, 15))
    length = rng.choice(range(7 * 60 + 30, 9 * 60 + 31, 15))
    if rng.random() < 0.4:
        # Lunch break: two intervals.
        lunch = rng.choice(range(12 * 60 + 30, 13 * 60 + 31, 15))
        back = lunch + rng.choice((30, 45, 60))
        return [
            {"entry": _time(start), "exit": _time(lunch)},
            {"entry": _time(back), "exit": _time(back + length - (lunch - start))},
        ]
    return [{"entry": _time(start), "exit": _time(start + length)}]


def _holiday_dates(first: date, last: date) -> Set[date]:
    for year in range(first.year, last.year + 1):
        ensure_holidays(year)
    rows = Holiday.query.filter(Holiday.date.between(first, last)).all()
    return {row.date for row in rows}


def seed_demo_entries(
    months: int = 3, today: Optional[date] = None, seed: int = 42
) -> int:
    """Create sample entries for the weekdays of the last `months` months.

    Returns the number of days created.
    """
    today = today or date.today()
    first = (today.replace(day=1) - timedelta(days=31 * (months - 1))).replace(day=1)
    last = today - timedelta(days=1)
    if last < first:
        return 0

    rng = random.Random(seed)
    holidays = _holiday_dates(first, last)
    existing = {
        row.date
        for row in ScheduleEntry.query.filter(
            ScheduleEntry.employee_id == DEFAULT_EMPLOYEE_ID,
            ScheduleEntry.date.between(first, last),
        )
    }

    # One vacation week in the first month and a sick day in the second.
    vacation_start = first + timedelta(days=14 - first.weekday())
    vacation = {vacation_start + timedelta(days=i) for i in range(5)}
    sick_day = vacation_start + timedelta(days=30)

    created = 0
    day = first
    while day <= last:
        if day.weekday() < 5 and day not in holidays and day not in existing:
            entries: List[dict] = []
            absence_code = observation = None
            if day in vacation:
                absence_code = "Vacation"
            elif day == sick_day:
                absence_code = "Sick Leave"
            else:
                entries = _workday(rng)
                if rng.random() < 0.1:
                    observation = rng.choice(OBSERVATIONS)
            entry = ScheduleEntry(
                employee_id=DEFAULT_EMPLOYEE_ID,
                date=day,
                entries=entries,
                absence_code=absence_code,
                observation=observation,
            )
            db.session.add(entry)
            created += 1
        day += timedelta(days=1)

    db.session.commit()
    return created
