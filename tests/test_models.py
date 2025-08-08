import unittest
from datetime import date
from typing import List

from app.db.database import db
from app.models.models import AbsenceCode, Employee, Holiday, ScheduleEntry


class TestModels(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.config.config import Config

        class TestConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

        self.app = create_app(TestConfig)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_employee_model(self):
        with self.app.app_context():
            employee = Employee(name="Test Employee")
            db.session.add(employee)
            db.session.commit()
            saved_employee = Employee.query.filter_by(name="Test Employee").first()
            self.assertIsNotNone(saved_employee)
            self.assertEqual(saved_employee.name, "Test Employee")

    def test_schedule_entry_model(self):
        with self.app.app_context():
            employee = Employee(name="Test Employee")
            db.session.add(employee)
            db.session.commit()

            entry_date = date(2025, 3, 16)
            entry_data = [{"entry": "09:00", "exit": "17:00"}]
            schedule_entry = ScheduleEntry(
                employee_id=employee.id,
                date=entry_date,
                entries=entry_data,
                absence_code=None,
            )
            db.session.add(schedule_entry)
            db.session.commit()

            saved_entry = ScheduleEntry.query.filter_by(date=entry_date).first()
            self.assertIsNotNone(saved_entry)
            self.assertEqual(saved_entry.employee_id, employee.id)
            self.assertEqual(saved_entry.date, entry_date)
            self.assertEqual(saved_entry.entries, entry_data)
            self.assertIsNone(saved_entry.absence_code)
            self.assertEqual(saved_entry.employee, employee)

            # Use the modern db.session.get() to avoid legacy warnings
            refreshed_employee = db.session.get(Employee, employee.id)
            self.assertIsNotNone(refreshed_employee)

            self.assertTrue(hasattr(refreshed_employee, "schedule_entries"))
            entries_list = list(refreshed_employee.schedule_entries)
            self.assertEqual(len(entries_list), 1)
            self.assertEqual(entries_list[0].id, saved_entry.id)

    def test_holiday_model(self):
        with self.app.app_context():
            holiday_date = date(2025, 1, 1)
            holiday = Holiday(
                date=holiday_date, description="New Year's Day", type="National"
            )
            db.session.add(holiday)
            db.session.commit()
            saved_holiday = Holiday.query.filter_by(date=holiday_date).first()
            self.assertIsNotNone(saved_holiday)

    def test_absence_code_model(self):
        with self.app.app_context():
            absence_code = AbsenceCode(code="SICK", description="Sick Leave")
            db.session.add(absence_code)
            db.session.commit()
            saved_code = AbsenceCode.query.filter_by(code="SICK").first()
            self.assertIsNotNone(saved_code)


if __name__ == "__main__":
    unittest.main()
