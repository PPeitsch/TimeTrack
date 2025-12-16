"""Tests for app/utils/init_data.py."""

import pytest

from app import create_app
from app.config.config import Config
from app.db.database import db
from app.models.models import AbsenceCode, Employee
from app.utils.init_data import DEFAULT_ABSENCE_CODES, init_data


class TestConfig(Config):
    """Test configuration for Flask app."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class TestInitData:
    """Tests for the init_data function."""

    @pytest.fixture
    def app(self):
        """Create and configure a Flask app for testing."""
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    def test_init_data_creates_default_employee(self, app):
        """Test that init_data creates the default employee."""
        with app.app_context():
            # Verify no employee exists before
            assert Employee.query.get(1) is None

            init_data()

            employee = Employee.query.get(1)
            assert employee is not None
            assert employee.name == "Default User"

    def test_init_data_creates_absence_codes(self, app):
        """Test that init_data creates all default absence codes."""
        with app.app_context():
            # Verify no codes exist before
            assert AbsenceCode.query.count() == 0

            init_data()

            codes = AbsenceCode.query.all()
            code_names = [c.code for c in codes]
            assert len(codes) == len(DEFAULT_ABSENCE_CODES)
            for expected_code in DEFAULT_ABSENCE_CODES:
                assert expected_code in code_names

    def test_init_data_is_idempotent(self, app):
        """Test that running init_data twice doesn't create duplicates."""
        with app.app_context():
            init_data()
            init_data()  # Run again

            # Should still have only one default employee
            employees = Employee.query.all()
            assert len(employees) == 1

            # Should still have the same number of codes
            codes = AbsenceCode.query.all()
            assert len(codes) == len(DEFAULT_ABSENCE_CODES)

    def test_init_data_skips_existing_employee(self, app):
        """Test that init_data doesn't overwrite existing employee."""
        with app.app_context():
            # Create employee first with different name
            existing_employee = Employee(id=1, name="Existing User")
            db.session.add(existing_employee)
            db.session.commit()

            init_data()

            # Employee name should remain unchanged
            employee = Employee.query.get(1)
            assert employee.name == "Existing User"

    def test_init_data_skips_existing_codes(self, app):
        """Test that init_data doesn't duplicate existing codes."""
        with app.app_context():
            # Create one code first
            existing_code = AbsenceCode(code="Vacation")
            db.session.add(existing_code)
            db.session.commit()
            existing_id = existing_code.id

            init_data()

            # The existing code should not be duplicated
            vacation_codes = AbsenceCode.query.filter_by(code="Vacation").all()
            assert len(vacation_codes) == 1
            assert vacation_codes[0].id == existing_id

    def test_init_data_rollback_on_error(self, app, mocker):
        """Test that init_data rolls back on error."""
        with app.app_context():
            # Mock commit to raise an error
            mocker.patch.object(db.session, "commit", side_effect=Exception("DB Error"))
            mocker.patch.object(db.session, "rollback")

            with pytest.raises(Exception, match="DB Error"):
                init_data()

            db.session.rollback.assert_called_once()

    def test_default_absence_codes_constant(self):
        """Test that DEFAULT_ABSENCE_CODES contains expected values."""
        assert "Vacation" in DEFAULT_ABSENCE_CODES
        assert "Sick Leave" in DEFAULT_ABSENCE_CODES
        assert "Personal Leave" in DEFAULT_ABSENCE_CODES
        assert len(DEFAULT_ABSENCE_CODES) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
