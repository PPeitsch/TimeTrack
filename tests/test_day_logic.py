"""Tests for the shared day logic, holiday sync and the data-safety fixes."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.db.database import db
from app.models.models import AbsenceCode, Holiday, HolidayYear, ScheduleEntry
from app.routes.import_log import _apply_records
from app.services import holiday_sync
from app.services.calendar_service import resolve_day, resolve_days, summarize
from app.services.importer.protocol import TimeEntryRecord

SATURDAY = date(2025, 3, 15)
MONDAY = date(2025, 3, 17)
HOLIDAY_DATE = date(2025, 3, 24)


def add_entry(day, entries=None, absence_code=None, observation=None):
    entry = ScheduleEntry(
        employee_id=1,
        date=day,
        entries=entries or [],
        absence_code=absence_code,
        observation=observation,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


class TestResolveDays:
    def test_weekend_work_counts_as_overtime(self, app, default_employee_id):
        add_entry(SATURDAY, [{"entry": "09:00", "exit": "13:00"}])
        day = resolve_day(1, SATURDAY)
        assert day.type == "Work Day"
        assert day.worked == 4.0
        assert day.required == 0.0

    def test_holiday_work_counts_as_overtime(self, app, default_employee_id):
        db.session.add(Holiday(date=HOLIDAY_DATE, description="Feriado"))
        add_entry(HOLIDAY_DATE, [{"entry": "09:00", "exit": "11:00"}])
        day = resolve_day(1, HOLIDAY_DATE)
        assert (day.worked, day.required) == (2.0, 0.0)

    def test_holiday_without_entry(self, app, default_employee_id):
        db.session.add(Holiday(date=HOLIDAY_DATE, description="Feriado"))
        db.session.commit()
        day = resolve_day(1, HOLIDAY_DATE)
        assert (day.type, day.required) == ("Holiday", 0.0)

    def test_absence_requires_nothing(self, app, default_employee_id):
        add_entry(MONDAY, absence_code="Vacation")
        day = resolve_day(1, MONDAY)
        assert (day.type, day.worked, day.required) == ("Vacation", 0.0, 0.0)

    def test_hours_per_day_comes_from_config(self, app, default_employee_id):
        app.config["WORKING_HOURS_PER_DAY"] = 6
        assert resolve_day(1, MONDAY).required == 6.0

    def test_views_agree_on_weekend_work(self, client, app, default_employee_id):
        add_entry(SATURDAY, [{"entry": "09:00", "exit": "13:00"}])
        calendar = client.get("/monthly-log/api/2025/3").get_json()
        assert {"date": "2025-03-15", "type": "Work Day"} in calendar
        daily = client.get("/summary/daily/2025-03-15").get_json()
        assert daily["hours"] == 4.0
        monthly = client.get("/summary/monthly/2025/3").get_json()
        assert monthly["total"] == 4.0

    def test_summarize(self, app, default_employee_id):
        add_entry(MONDAY, [{"entry": "09:00", "exit": "18:00"}])
        days = resolve_days(1, MONDAY, MONDAY)
        assert summarize(days) == {"total": 9.0, "required": 8.0, "difference": 1.0}


class TestHolidaySync:
    @pytest.fixture(autouse=True)
    def enable_fetch(self, app):
        app.config["HOLIDAY_AUTO_FETCH"] = True
        holiday_sync._failed_fetches.clear()

    def provider_with(self, holidays):
        provider = MagicMock()
        provider.get_holidays.return_value = holidays
        return patch(
            "app.services.holiday_sync.get_holiday_provider", return_value=provider
        )

    def test_fetches_missing_year_once(self, app):
        with self.provider_with([Holiday(date=date(2031, 1, 1), description="New")]):
            holiday_sync.ensure_holidays(2031)
            holiday_sync.ensure_holidays(2031)
        assert Holiday.query.count() == 1
        assert db.session.get(HolidayYear, 2031) is not None

    def test_failure_is_not_retried_immediately(self, app):
        with self.provider_with([]) as factory:
            holiday_sync.ensure_holidays(2032)
            holiday_sync.ensure_holidays(2032)
        assert factory.call_count == 1
        assert db.session.get(HolidayYear, 2032) is None

    def test_existing_rows_mark_the_year(self, app):
        db.session.add(Holiday(date=date(2033, 5, 1), description="Old"))
        db.session.commit()
        with self.provider_with([]) as factory:
            holiday_sync.ensure_holidays(2033)
        factory.assert_not_called()
        assert db.session.get(HolidayYear, 2033) is not None

    def test_refresh_keeps_data_when_provider_is_empty(self, app):
        db.session.add(Holiday(date=date(2034, 5, 1), description="Old"))
        db.session.commit()
        with self.provider_with([]):
            with pytest.raises(RuntimeError):
                holiday_sync.refresh_holidays(2034)
        assert Holiday.query.count() == 1

    def test_cli_refresh(self, app):
        with self.provider_with([Holiday(date=date(2035, 7, 9), description="X")]):
            result = app.test_cli_runner().invoke(args=["holidays", "refresh", "2035"])
        assert result.exit_code == 0, result.output
        assert "2035: 1 holidays loaded." in result.output


class TestDataSafety:
    def test_renaming_code_updates_days(self, client, app, default_employee_id):
        code = AbsenceCode(code="Vacation")
        db.session.add(code)
        db.session.commit()
        add_entry(MONDAY, absence_code="Vacation")

        response = client.put(
            f"/settings/api/absence-codes/{code.id}", json={"code": "Holidays off"}
        )
        assert response.status_code == 200
        assert ScheduleEntry.query.one().absence_code == "Holidays off"

    def test_default_keeps_logged_hours(self, client, app, default_employee_id):
        add_entry(SATURDAY, [{"entry": "09:00", "exit": "13:00"}], observation="x")
        add_entry(MONDAY)
        response = client.post(
            "/monthly-log/api/update-days",
            json={"dates": ["2025-03-15", "2025-03-17"], "day_type": "DEFAULT"},
        )
        assert response.status_code == 200
        remaining = ScheduleEntry.query.all()
        assert [e.date for e in remaining] == [SATURDAY]
        assert remaining[0].entries == [{"entry": "09:00", "exit": "13:00"}]


class TestImportMerge:
    def record(self, day="2025-03-17", entry=None, exit=None, obs=None):
        return TimeEntryRecord(
            date=day, entry_time=entry, exit_time=exit, observation=obs
        )

    def test_record_without_times_keeps_hours(self, app, default_employee_id):
        add_entry(MONDAY, [{"entry": "09:00", "exit": "17:00"}])
        imported, skipped = _apply_records(
            [self.record(obs="Late bus")], 1, "overwrite"
        )
        entry = ScheduleEntry.query.one()
        assert entry.entries == [{"entry": "09:00", "exit": "17:00"}]
        assert entry.observation == "Late bus"
        assert (imported, skipped) == (1, 0)

    def test_empty_record_is_skipped(self, app, default_employee_id):
        assert _apply_records([self.record()], 1, "overwrite") == (0, 1)
        assert ScheduleEntry.query.count() == 0

    def test_skip_mode_leaves_existing_days(self, app, default_employee_id):
        add_entry(MONDAY, [{"entry": "09:00", "exit": "17:00"}])
        record = self.record(entry="10:00", exit="12:00")
        assert _apply_records([record], 1, "skip") == (0, 1)
        assert ScheduleEntry.query.one().entries[0]["entry"] == "09:00"

    def test_overwrite_mode_replaces_times(self, app, default_employee_id):
        add_entry(MONDAY, absence_code="Vacation")
        record = self.record(entry="10:00", exit="12:00")
        assert _apply_records([record], 1, "overwrite") == (1, 0)
        entry = ScheduleEntry.query.one()
        assert entry.absence_code is None
        assert entry.entries == [{"entry": "10:00", "exit": "12:00"}]


def test_parse_flags_invalid_times(app, tmp_path):
    from app.routes.import_log import _parse
    from app.services.importer.protocol import ImportResult

    records = [
        TimeEntryRecord(date="2025-03-17", entry_time="17:00", exit_time="09:00"),
        TimeEntryRecord(date="2025-03-18", entry_time="09:00"),
        TimeEntryRecord(date="2025-03-19", entry_time="09:00", exit_time="17:00"),
    ]
    importer = MagicMock()
    importer.parse.return_value = ImportResult(
        records=records, total_records=3, valid_records=3, errors=[]
    )
    path = tmp_path / "file.xlsx"
    path.write_bytes(b"")
    with patch(
        "app.routes.import_log.ImporterFactory.get_importer", return_value=importer
    ):
        result = _parse(str(path))
    assert [r.is_valid for r in result.records] == [False, False, True]
    assert result.valid_records == 1
