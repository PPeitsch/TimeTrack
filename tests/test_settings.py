import json
from datetime import date

from app.db.database import db
from app.models.models import AbsenceCode, ScheduleEntry


class TestSettingsRoutes:
    """Tests for the settings and absence code management feature."""

    def test_manage_absences_page(self, client):
        """Test that the settings page for absences loads correctly."""
        response = client.get("/settings/absences")
        assert response.status_code == 200
        assert b"Add New Absence Code" in response.data

    def test_get_absence_codes_api(self, app):
        """Test GET all absence codes are returned and ordered correctly."""
        with app.app_context():
            # Create codes out of order to test sorting
            db.session.add(AbsenceCode(code="Z-CODE"))
            db.session.add(AbsenceCode(code="A-CODE"))
            db.session.commit()

        client = app.test_client()
        response = client.get("/settings/api/absence-codes")
        assert response.status_code == 200
        data = json.loads(response.data)

        # We expect at least the two codes we created
        assert len(data) >= 2
        # Verify they are sorted alphabetically by code
        assert data[0]["code"] == "A-CODE"
        assert data[-1]["code"] == "Z-CODE"

    def test_create_absence_code_api(self, client):
        """Test POST to create a new absence code."""
        payload = {"code": "NEW-TEST-CODE"}
        response = client.post("/settings/api/absence-codes", json=payload)

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["code"] == "NEW-TEST-CODE"
        assert "id" in data

    def test_create_absence_code_api_conflict(self, app):
        """Test that creating a code that already exists returns a conflict."""
        client = app.test_client()
        # Pre-condition: Create the code first
        with app.app_context():
            db.session.add(AbsenceCode(code="EXISTING-CODE"))
            db.session.commit()

        payload = {"code": "EXISTING-CODE"}
        response = client.post("/settings/api/absence-codes", json=payload)
        assert response.status_code == 409

    def test_update_absence_code_api(self, app):
        """Test PUT to update an absence code."""
        client = app.test_client()
        # Pre-condition: Create the code to be updated
        with app.app_context():
            code = AbsenceCode(code="OLD-NAME")
            db.session.add(code)
            db.session.commit()
            code_id = code.id

        payload = {"code": "NEW-NAME"}
        response = client.put(f"/settings/api/absence-codes/{code_id}", json=payload)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["code"] == "NEW-NAME"

    def test_delete_absence_code_api(self, app):
        """Test DELETE to remove an absence code."""
        client = app.test_client()
        # Pre-condition: Create the code to be deleted
        with app.app_context():
            code_to_delete = AbsenceCode(code="TO-DELETE")
            db.session.add(code_to_delete)
            db.session.commit()
            code_id = code_to_delete.id

        response = client.delete(f"/settings/api/absence-codes/{code_id}")
        assert response.status_code == 200

        # Verify it's gone
        with app.app_context():
            code = db.session.get(AbsenceCode, code_id)
            assert code is None

    def test_delete_absence_code_in_use(self, app, default_employee_id):
        """Test that a code in use cannot be deleted."""
        client = app.test_client()
        # Pre-conditions: Create the code and a schedule entry that uses it
        with app.app_context():
            code_in_use = AbsenceCode(code="IN-USE-CODE")
            db.session.add(code_in_use)
            db.session.commit()
            code_id = code_in_use.id

            # Use a proper date object, not a string
            schedule_entry = ScheduleEntry(
                employee_id=default_employee_id,
                date=date(2025, 10, 10),
                absence_code="IN-USE-CODE",
            )
            db.session.add(schedule_entry)
            db.session.commit()

        response = client.delete(f"/settings/api/absence-codes/{code_id}")
        assert response.status_code == 409
        data = json.loads(response.data)
        assert "Cannot delete code, it is currently in use" in data["error"]
