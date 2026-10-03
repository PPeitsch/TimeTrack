"""Load public holidays into the database, one year at a time.

Years are fetched lazily the first time a view needs them (so the calendar keeps
working after the year changes) and can be refreshed with
`flask holidays refresh [YEAR ...]`.
"""

import logging
import time
from datetime import date, datetime
from types import SimpleNamespace
from typing import Dict, Iterable, List

import click
from flask import current_app
from flask.cli import with_appcontext

from app.db.database import db
from app.models.models import Holiday, HolidayYear
from app.services.holiday_service import get_holiday_provider

logger = logging.getLogger(__name__)

# Years whose last fetch failed, with the time of the failure, so a provider that
# is down does not slow every request (the provider timeout is 10 s).
_failed_fetches: Dict[int, float] = {}
RETRY_AFTER_SECONDS = 3600


def ensure_holidays(year: int) -> None:
    """Make sure the holidays of `year` are loaded, fetching them if needed."""
    if not current_app.config.get("HOLIDAY_AUTO_FETCH", True):
        return
    if db.session.get(HolidayYear, year) is not None:
        return
    if _year_query(year).first() is not None:
        # Loaded by an older version of init_db.py: just mark the year.
        _mark_year(year)
        db.session.commit()
        return
    failed_at = _failed_fetches.get(year)
    if failed_at is not None and time.monotonic() - failed_at < RETRY_AFTER_SECONDS:
        return
    try:
        refresh_holidays(year)
    except Exception:
        db.session.rollback()
        _failed_fetches[year] = time.monotonic()
        logger.exception("Could not load holidays for %s", year)


def refresh_holidays(year: int) -> int:
    """Replace the stored holidays of `year` with the provider's. Returns the count.

    Raises RuntimeError when the provider returns nothing, leaving the stored
    holidays untouched.
    """
    provider = get_holiday_provider(SimpleNamespace(**current_app.config))  # type: ignore[arg-type]
    fetched: List[Holiday] = provider.get_holidays(year)
    unique = {h.date: h for h in fetched if h.date.year == year}
    if not unique:
        raise RuntimeError(f"The holiday provider returned no holidays for {year}")

    _year_query(year).delete(synchronize_session=False)
    db.session.add_all(
        Holiday(date=h.date, description=h.description, type=h.type)
        for h in unique.values()
    )
    _mark_year(year)
    db.session.commit()
    _failed_fetches.pop(year, None)
    return len(unique)


def _year_query(year: int):
    return Holiday.query.filter(
        Holiday.date.between(date(year, 1, 1), date(year, 12, 31))
    )


def _mark_year(year: int) -> None:
    marker = db.session.get(HolidayYear, year)
    if marker is None:
        db.session.add(HolidayYear(year=year, fetched_at=datetime.utcnow()))
    else:
        marker.fetched_at = datetime.utcnow()


@click.group("holidays")
def holidays_cli():
    """Manage public holidays."""


@holidays_cli.command("refresh")
@click.argument("years", nargs=-1, type=int)
@with_appcontext
def refresh_command(years: Iterable[int]) -> None:
    """Reload holidays for YEARS (default: current and next year)."""
    current = date.today().year
    for year in years or (current, current + 1):
        try:
            count = refresh_holidays(year)
            click.echo(f"{year}: {count} holidays loaded.")
        except Exception as error:
            db.session.rollback()
            raise click.ClickException(f"{year}: {error}")
