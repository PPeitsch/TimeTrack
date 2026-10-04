"""Tests for the four main screens and the day API used by the calendar."""

from datetime import date

import pytest

from app.db.database import db
from app.models.models import AbsenceCode, ScheduleEntry
from app.utils.time_calculator import format_hours


@pytest.fixture
def vacation(app):
    db.session.add(AbsenceCode(code="Vacation"))
    db.session.commit()


class TestScreens:
    @pytest.mark.parametrize("url", ["/", "/calendar", "/reports", "/settings"])
    def test_screen_renders(self, client, default_employee_id, url):
        response = client.get(url)
        assert response.status_code == 200
        assert b'aria-current="page"' in response.data

    def test_reports_month_and_totals(self, client, default_employee_id):
        db.session.add(
            ScheduleEntry(
                employee_id=1,
                date=date(2025, 3, 17),
                entries=[{"entry": "09:00", "exit": "18:30"}],
            )
        )
        db.session.commit()
        html = client.get("/reports?ym=2025-03").get_data(as_text=True)
        assert "09:00-18:30" in html
        assert "9:30" in html

    def test_reports_bad_month_falls_back(self, client, default_employee_id):
        assert client.get("/reports?ym=nope").status_code == 200

    def test_csv_export(self, client, default_employee_id):
        response = client.get("/reports/export.csv?year=2025&month=2")
        assert response.mimetype == "text/csv"
        assert "timetrack-2025-02.csv" in response.headers["Content-Disposition"]
        lines = response.get_data(as_text=True).strip().splitlines()
        assert lines[0].startswith("date,type")
        assert len(lines) == 1 + 28


class TestDayApi:
    def test_month_days(self, client, default_employee_id):
        data = client.get("/api/days/2025/3").get_json()
        assert len(data["days"]) == 31
        assert data["days"][0]["base_type"] == "Weekend"  # 2025-03-01 is Saturday
        assert data["summary"]["required"] == 21 * 8.0

    def test_invalid_month(self, client, default_employee_id):
        assert client.get("/api/days/2025/13").status_code == 400

    def test_save_work_day_with_observation(self, client, default_employee_id):
        response = client.put(
            "/api/days/2025-03-17",
            json={
                "kind": "work",
                "entries": [{"entry": "09:00", "exit": "13:00"}],
                "observation": "Dentist in the afternoon",
            },
        )
        assert response.status_code == 200
        day = response.get_json()
        assert day["worked"] == 4.0
        assert day["observation"] == "Dentist in the afternoon"

    def test_save_rejects_bad_times(self, client, default_employee_id):
        response = client.put(
            "/api/days/2025-03-17",
            json={"kind": "work", "entries": [{"entry": "09:00", "exit": "09:00"}]},
        )
        assert response.status_code == 400

    def test_save_absence(self, client, default_employee_id, vacation):
        response = client.put(
            "/api/days/2025-03-17", json={"kind": "absence", "absence_code": "Vacation"}
        )
        assert response.get_json()["type"] == "Vacation"

    def test_save_unknown_absence(self, client, default_employee_id):
        response = client.put(
            "/api/days/2025-03-17", json={"kind": "absence", "absence_code": "Nope"}
        )
        assert response.status_code == 400

    def test_default_removes_override_but_keeps_note(self, client, default_employee_id):
        client.put("/api/days/2025-03-17", json={"kind": "work", "entries": []})
        client.put(
            "/api/days/2025-03-17", json={"kind": "default", "observation": "keep me"}
        )
        entry = ScheduleEntry.query.one()
        assert entry.observation == "keep me" and entry.entries == []

        client.put("/api/days/2025-03-17", json={"kind": "default"})
        assert ScheduleEntry.query.count() == 0

    def test_invalid_kind_and_date(self, client, default_employee_id):
        assert client.put("/api/days/2025-03-17", json={"kind": "x"}).status_code == 400
        assert client.put("/api/days/bad", json={"kind": "work"}).status_code == 400


@pytest.mark.parametrize(
    "hours,signed,expected",
    [
        (7.5, False, "7:30"),
        (-0.25, False, "-0:15"),
        (1, True, "+1:00"),
        (0, True, "0:00"),
    ],
)
def test_format_hours(hours, signed, expected):
    assert format_hours(hours, signed) == expected
