import os
import sys

import pytest

# Add the parent directory to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config.config import Config
from app.db.database import db
from app.models.models import Employee, ScheduleEntry


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def default_employee(app):
    """Create a default employee for testing."""
    with app.app_context():
        employee = Employee(id=1, name="Default Test Employee")
        db.session.add(employee)
        db.session.commit()
        return employee


@pytest.fixture
def sample_entries(app, default_employee):
    """Create sample time entries for testing."""
    with app.app_context():
        # Add some test data
        entries = []

        # Regular work day
        entry1 = ScheduleEntry(
            employee_id=default_employee.id,
            date="2025-03-10",  # Monday
            entries=[{"entry": "09:00", "exit": "17:00"}],
            absence_code=None,
        )
        db.session.add(entry1)
        entries.append(entry1)

        # Absence day
        entry2 = ScheduleEntry(
            employee_id=default_employee.id,
            date="2025-03-11",  # Tuesday
            entries=[],
            absence_code="SICK",
        )
        db.session.add(entry2)
        entries.append(entry2)

        # Multiple time entries in one day
        entry3 = ScheduleEntry(
            employee_id=default_employee.id,
            date="2025-03-12",  # Wednesday
            entries=[
                {"entry": "09:00", "exit": "12:00"},
                {"entry": "13:00", "exit": "18:00"},
            ],
            absence_code=None,
        )
        db.session.add(entry3)
        entries.append(entry3)

        db.session.commit()
        return entries
