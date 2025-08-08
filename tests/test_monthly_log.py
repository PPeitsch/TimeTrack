import json
from datetime import date

import pytest

from app.db.database import db
from app.models.models import AbsenceCode, Holiday, ScheduleEntry


class TestMonthlyLogRoutes:
    """Tests for the monthly log calendar feature."""

    def test_view_monthly_log_page(self, client):
        """Test that the main calendar page loads correctly."""
        response = client.get("/monthly-log/")
        assert response.status_code == 200
        assert b"Monthly Log Management" in response.data

    def test_get_absence_codes_api_is_moved(self, app):
        """Test that the old absence codes API URL is no longer available."""
        client = app.test_client()
        response = client.get("/monthly-log/api/absence-codes")
        assert response.status_code == 404

    def test_get_monthly_log_data_api(self, app, default_employee_id):
        """Test that the API returns correct day types for a month."""
        with app.app_context():
            db.session.add(
                ScheduleEntry(
                    employee_id=default_employee_id,
                    date=date(2025, 8, 4),
                    absence_code="VACATION",
                    entries=[],
                )
            )
            db.session.add(Holiday(date=date(2025, 8, 15), description="Test Holiday"))
            db.session.commit()

        client = app.test_client()
        response = client.get("/monthly-log/api/2025/8")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 31

        day_map = {item["date"]: item["type"] for item in data}
        assert day_map["2025-08-04"] == "VACATION"
        assert day_map["2025-08-15"] == "Holiday"
        assert day_map["2025-08-09"] == "Weekend"
        assert day_map["2025-08-11"] == "Work Day"

    def test_get_monthly_log_data_api_exception(self, client, mocker):
        """Test exception handling for the monthly log data API."""
        mocker.patch(
            "app.routes.monthly_log.ScheduleEntry.query"
        ).filter.return_value.all.side_effect = Exception("DB Error")
        response = client.get("/monthly-log/api/2025/8")
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["error"] == "DB Error"

    def test_update_day_types_api_creates_and_reverts(self, app, default_employee_id):
        """Test creating a new absence and reverting it to a work day."""
        client = app.test_client()
        target_date = date(2025, 9, 1)

        payload_create = {"dates": [target_date.isoformat()], "day_type": "LAR"}
        client.post("/monthly-log/api/update-days", json=payload_create)
        with app.app_context():
            entry = ScheduleEntry.query.filter_by(
                date=target_date, employee_id=default_employee_id
            ).first()
            assert entry is not None and entry.absence_code == "LAR"

        payload_revert = {"dates": [target_date.isoformat()], "day_type": "DEFAULT"}
        client.post("/monthly-log/api/update-days", json=payload_revert)
        with app.app_context():
            entry = ScheduleEntry.query.filter_by(
                date=target_date, employee_id=default_employee_id
            ).first()
            assert entry is None

    def test_update_day_types_modifies_existing(self, app, default_employee_id):
        """Test that updating an existing entry to an absence clears its time entries."""
        client = app.test_client()
        target_date = date(2025, 9, 5)

        # 1. Create an initial entry with some time data
        with app.app_context():
            initial_entry = ScheduleEntry(
                employee_id=default_employee_id,
                date=target_date,
                entries=[{"entry": "09:00", "exit": "17:00"}],
                absence_code=None,
            )
            db.session.add(initial_entry)
            db.session.commit()

        # 2. Call the API to change the day type to an absence
        payload_update = {"dates": [target_date.isoformat()], "day_type": "MEDICAL"}
        response = client.post("/monthly-log/api/update-days", json=payload_update)
        assert response.status_code == 200

        # 3. Verify the entry was updated and its time entries were cleared
        with app.app_context():
            updated_entry = ScheduleEntry.query.filter_by(date=target_date).first()
            assert updated_entry is not None
            assert updated_entry.absence_code == "MEDICAL"
            assert updated_entry.entries == []

    def test_update_day_types_api_exception(self, client, mocker, default_employee_id):
        """Test exception handling for the update day types API."""
        mocker.patch("app.routes.monthly_log.db.session.commit").side_effect = (
            Exception("Commit Failed")
        )
        mocker.patch("app.routes.monthly_log.db.session.rollback")

        payload = {"dates": ["2025-09-02"], "day_type": "MEDICAL"}
        response = client.post("/monthly-log/api/update-days", json=payload)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["error"] == "Commit Failed"
        db.session.rollback.assert_called_once()

    def test_update_day_types_bad_request(self, client):
        """Test that the update endpoint handles bad requests."""
        payload = {"invalid_key": "some_value"}
        response = client.post("/monthly-log/api/update-days", json=payload)
        assert response.status_code == 400
