import json
import unittest
from datetime import date, datetime

from app.db.database import db
from app.models.models import Employee, ScheduleEntry


class TestRoutes(unittest.TestCase):
    def setUp(self):
        # Configure a test app
        from app import create_app
        from app.config.config import Config

        class TestConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create a default employee
            employee = Employee(id=1, name="Default Employee")
            db.session.add(employee)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        # Test the index route
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_manual_entry_route_get(self):
        # Test the manual entry form route
        response = self.client.get("/entry")
        self.assertEqual(response.status_code, 200)

    def test_manual_entry_route_post(self):
        # Test posting a new time entry
        entry_data = {
            "date": "2025-03-16",
            "employee_id": 1,
            "entries": [{"entry": "09:00", "exit": "17:00"}],
            "absence_code": None,
        }

        response = self.client.post(
            "/entry", data=json.dumps(entry_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")

        # Verify the entry was created in the database
        with self.app.app_context():
            entry = ScheduleEntry.query.filter_by(
                date=datetime.strptime("2025-03-16", "%Y-%m-%d").date()
            ).first()
            self.assertIsNotNone(entry)
            self.assertEqual(entry.employee_id, 1)
            self.assertEqual(len(entry.entries), 1)
            self.assertEqual(entry.entries[0]["entry"], "09:00")
            self.assertEqual(entry.entries[0]["exit"], "17:00")

    def test_manual_entry_route_post_invalid(self):
        # Test posting invalid data
        invalid_data = {
            "date": "2025-03-16",
            "employee_id": 1,
            "entries": [
                {"entry": "17:00", "exit": "09:00"}  # Exit before entry (invalid)
            ],
            "absence_code": None,
        }

        response = self.client.post(
            "/entry", data=json.dumps(invalid_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_time_summary_route(self):
        # Test the time summary route
        response = self.client.get("/summary/")
        self.assertEqual(response.status_code, 200)

    def test_time_logs_route(self):
        # Test the time logs route
        response = self.client.get("/logs/")
        self.assertEqual(response.status_code, 200)

    def test_daily_summary_route(self):
        # Create a test entry first
        with self.app.app_context():
            entry_date = date(2025, 3, 16)
            schedule_entry = ScheduleEntry(
                employee_id=1,
                date=entry_date,
                entries=[{"entry": "09:00", "exit": "17:00"}],
                absence_code=None,
            )
            db.session.add(schedule_entry)
            db.session.commit()

        # Test getting daily summary
        response = self.client.get("/summary/daily/2025-03-16")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Weekend day (Sunday March 16, 2025)
        self.assertEqual(data["hours"], 8.0)
        self.assertEqual(data["required"], 0.0)  # Weekend
        self.assertEqual(data["difference"], 8.0)

    def test_monthly_summary_route(self):
        # Create some test entries for the month
        with self.app.app_context():
            # Add a workday entry
            workday_date = date(2025, 3, 10)  # A Monday
            workday_entry = ScheduleEntry(
                employee_id=1,
                date=workday_date,
                entries=[{"entry": "09:00", "exit": "17:00"}],
                absence_code=None,
            )
            db.session.add(workday_entry)

            # Add an absence day
            absence_date = date(2025, 3, 11)  # A Tuesday
            absence_entry = ScheduleEntry(
                employee_id=1, date=absence_date, entries=[], absence_code="SICK"
            )
            db.session.add(absence_entry)

            db.session.commit()

        # Test getting monthly summary
        response = self.client.get("/summary/monthly/2025/3")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Check the response structure
        self.assertIn("total", data)
        self.assertIn("required", data)
        self.assertIn("difference", data)

    def test_monthly_logs_route(self):
        # Create a test entry first
        with self.app.app_context():
            entry_date = date(2025, 3, 16)
            schedule_entry = ScheduleEntry(
                employee_id=1,
                date=entry_date,
                entries=[{"entry": "09:00", "exit": "17:00"}],
                absence_code=None,
            )
            db.session.add(schedule_entry)
            db.session.commit()

        # Test getting monthly logs
        response = self.client.get("/logs/monthly/2025/3")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Check that we got a list with at least one entry
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

        # Check the structure of the first entry
        entry = data[0]
        self.assertIn("date", entry)
        self.assertIn("type", entry)
        self.assertIn("entries", entry)
        self.assertIn("total_hours", entry)


if __name__ == "__main__":
    unittest.main()
