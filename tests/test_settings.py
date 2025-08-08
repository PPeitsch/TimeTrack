import json
from datetime import date

import pytest

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
            db.session.add(AbsenceCode(code="Z-CODE"))
            db.session.add(AbsenceCode(code="A-CODE"))
            db.session.commit()

        client = app.test_client()
        response = client.get("/settings/api/absence-codes")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert len(data) >= 2
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

    @pytest.mark.parametrize(
        "payload", [({"code": "   "}), ({"code": ""}), ({"wrong_key": "v"}), ({})]
    )
    def test_create_absence_code_invalid_payloads(self, client, payload):
        """Test creating a code with various invalid payloads."""
        response = client.post("/settings/api/absence-codes", json=payload)
        assert response.status_code == 400

    def test_create_absence_code_api_conflict(self, app):
        """Test that creating a code that already exists returns a conflict."""
        client = app.test_client()
        with app.app_context():
            db.session.add(AbsenceCode(code="EXISTING-CODE"))
            db.session.commit()

        payload = {"code": "EXISTING-CODE"}
        response = client.post("/settings/api/absence-codes", json=payload)
        assert response.status_code == 409

    def test_update_absence_code_api(self, app):
        """Test PUT to update an absence code."""
        client = app.test_client()
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

    @pytest.mark.parametrize(
        "payload", [({"code": "   "}), ({"code": ""}), ({"wrong_key": "v"}), ({})]
    )
    def test_update_absence_code_invalid_payloads(self, client, payload):
        """Test updating a code with various invalid payloads."""
        # We only need an ID that exists for the endpoint to proceed to validation.
        # The actual ID doesn't matter since the request will fail before DB access.
        response = client.put("/settings/api/absence-codes/1", json=payload)
        assert response.status_code == 400

    def test_update_absence_code_not_found(self, client):
        """Test updating a code that does not exist."""
        response = client.put("/settings/api/absence-codes/999", json={"code": "ANY"})
        assert response.status_code == 404

    def test_update_absence_code_conflict(self, app):
        """Test updating a code to a name that already exists."""
        client = app.test_client()
        with app.app_context():
            db.session.add(AbsenceCode(code="CODE-A"))
            code_b = AbsenceCode(code="CODE-B")
            db.session.add(code_b)
            db.session.commit()
            code_b_id = code_b.id

        response = client.put(
            f"/settings/api/absence-codes/{code_b_id}", json={"code": "CODE-A"}
        )
        assert response.status_code == 409

    def test_delete_absence_code_api(self, app):
        """Test DELETE to remove an absence code."""
        client = app.test_client()
        with app.app_context():
            code_to_delete = AbsenceCode(code="TO-DELETE")
            db.session.add(code_to_delete)
            db.session.commit()
            code_id = code_to_delete.id

        response = client.delete(f"/settings/api/absence-codes/{code_id}")
        assert response.status_code == 200

        with app.app_context():
            code = db.session.get(AbsenceCode, code_id)
            assert code is None

    def test_delete_absence_code_not_found(self, client):
        """Test deleting a code that does not exist."""
        response = client.delete("/settings/api/absence-codes/999")
        assert response.status_code == 404

    def test_delete_absence_code_in_use(self, app, default_employee_id):
        """Test that a code in use cannot be deleted."""
        client = app.test_client()
        with app.app_context():
            code_in_use = AbsenceCode(code="IN-USE-CODE")
            db.session.add(code_in_use)
            db.session.commit()
            code_id = code_in_use.id

            schedule_entry = ScheduleEntry(
                employee_id=default_employee_id,
                date=date(2025, 10, 10),
                absence_code="IN-USE-CODE",
                entries=[],
            )
            db.session.add(schedule_entry)
            db.session.commit()

        response = client.delete(f"/settings/api/absence-codes/{code_id}")
        assert response.status_code == 409
        data = json.loads(response.data)
        assert "Cannot delete code, it is currently in use" in data["error"]

    def test_get_codes_db_error(self, client, mocker):
        """Test generic exception for GET endpoint."""
        mocker.patch("app.routes.settings.AbsenceCode.query").order_by.side_effect = (
            Exception("DB Error")
        )
        response = client.get("/settings/api/absence-codes")
        assert response.status_code == 500

    def test_create_code_db_error(self, client, mocker):
        """Test generic exception for POST endpoint."""
        mocker.patch("app.routes.settings.db.session.commit").side_effect = Exception(
            "DB Error"
        )
        response = client.post("/settings/api/absence-codes", json={"code": "ANY"})
        assert response.status_code == 500

    def test_update_code_db_error(self, app, mocker):
        """Test generic exception for PUT endpoint."""
        client = app.test_client()
        with app.app_context():
            code = AbsenceCode(code="ANY")
            db.session.add(code)
            db.session.commit()
            code_id = code.id
        mocker.patch("app.routes.settings.db.session.commit").side_effect = Exception(
            "DB Error"
        )
        response = client.put(
            f"/settings/api/absence-codes/{code_id}", json={"code": "NEW"}
        )
        assert response.status_code == 500

    def test_delete_code_db_error(self, app, mocker):
        """Test generic exception for DELETE endpoint."""
        client = app.test_client()
        with app.app_context():
            code = AbsenceCode(code="ANY")
            db.session.add(code)
            db.session.commit()
            code_id = code.id
        mocker.patch("app.routes.settings.db.session.commit").side_effect = Exception(
            "DB Error"
        )
        response = client.delete(f"/settings/api/absence-codes/{code_id}")
        assert response.status_code == 500
