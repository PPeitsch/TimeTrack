import json
from datetime import date

from app.db.database import db
from app.models.models import AbsenceCode, Holiday, ScheduleEntry


class TestMonthlyLogRoutes:
    """Tests for the monthly log calendar feature."""

    def test_view_monthly_log_page(self, client):
        """Test that the main calendar page loads correctly."""
        response = client.get("/monthly-log/")
        assert response.status_code == 200
        assert b"Monthly Log Management" in response.data

    def test_get_absence_codes_api(self, app):
        """Test that the API returns a list of absence codes."""
        with app.app_context():
            db.session.add(AbsenceCode(code="LAR"))
            db.session.add(AbsenceCode(code="MEDICAL"))
            db.session.commit()

        client = app.test_client()
        response = client.get("/monthly-log/api/absence-codes")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert "LAR" in data
        assert "MEDICAL" in data

    def test_get_monthly_log_data_api(self, app, default_employee):
        """Test that the API returns correct day types for a month."""
        with app.app_context():
            # Setup test data for August 2025
            # An absence day (Monday, Aug 4)
            db.session.add(
                ScheduleEntry(
                    employee_id=default_employee.id,
                    date=date(2025, 8, 4),
                    absence_code="VACATION",
                    entries=[],
                )
            )
            # A holiday (Friday, Aug 15)
            db.session.add(Holiday(date=date(2025, 8, 15), description="Test Holiday"))
            db.session.commit()

        client = app.test_client()
        response = client.get("/monthly-log/api/2025/8")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 31  # 31 days in August

        # Create a map for easy lookup
        day_map = {item["date"]: item["type"] for item in data}

        assert day_map["2025-08-04"] == "VACATION"  # Absence
        assert day_map["2025-08-15"] == "Holiday"  # Holiday
        assert day_map["2025-08-09"] == "Weekend"  # Saturday
        assert day_map["2025-08-11"] == "Work Day"  # A regular Monday

    def test_update_day_types_api(self, app, default_employee):
        """Test updating day types via the POST API."""
        client = app.test_client()

        # 1. Create a new absence entry
        payload_create = {"dates": ["2025-09-01"], "day_type": "LAR"}
        response = client.post("/monthly-log/api/update-days", json=payload_create)
        assert response.status_code == 200
        with app.app_context():
            entry = ScheduleEntry.query.filter_by(date=date(2025, 9, 1)).first()
            assert entry is not None
            assert entry.absence_code == "LAR"

        # 2. Update an existing entry to a new absence type
        payload_update = {"dates": ["2025-09-01"], "day_type": "MEDICAL"}
        response = client.post("/monthly-log/api/update-days", json=payload_update)
        assert response.status_code == 200
        with app.app_context():
            db.session.refresh(entry)
            assert entry.absence_code == "MEDICAL"

        # 3. Revert an absence back to a Work Day
        payload_revert = {"dates": ["2025-09-01"], "day_type": "Work Day"}
        response = client.post("/monthly-log/api/update-days", json=payload_revert)
        assert response.status_code == 200
        with app.app_context():
            db.session.refresh(entry)
            assert entry.absence_code is None

    def test_update_day_types_bad_request(self, client):
        """Test that the update endpoint handles bad requests."""
        payload = {"invalid_key": "some_value"}
        response = client.post("/monthly-log/api/update-days", json=payload)
        assert response.status_code == 400
