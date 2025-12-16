"""Tests for app/routes/import_log.py."""

import io
import json
import os
import tempfile
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from app.config.config import Config
from app.db.database import db
from app.models.models import Employee, ScheduleEntry
from app.services.importer.protocol import ImportResult, TimeEntryRecord


class TestConfig(Config):
    """Test configuration for Flask app."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class TestImportLogRoutes:
    """Tests for the import log feature."""

    @pytest.fixture
    def app(self):
        """Create and configure a Flask app for testing."""
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            # Create default employee
            employee = Employee(id=1, name="Default Employee")
            db.session.add(employee)
            db.session.commit()
            yield app
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        """A test client for the app."""
        return app.test_client()

    def test_upload_page_get(self, client):
        """Test that the upload page loads correctly."""
        response = client.get("/import/")
        assert response.status_code == 200

    def test_upload_no_file_part(self, client):
        """Test upload with no file part in request."""
        response = client.post("/import/", data={})
        assert response.status_code == 302  # Redirect
        assert b"redirect" in response.data.lower() or response.status_code == 302

    def test_upload_no_selected_file(self, client):
        """Test upload with empty filename."""
        data = {"file": (io.BytesIO(b""), "")}
        response = client.post(
            "/import/", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 302  # Redirect back

    def test_upload_unsupported_file_type(self, client):
        """Test upload with unsupported file type."""
        data = {"file": (io.BytesIO(b"content"), "file.txt")}
        response = client.post(
            "/import/", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 302  # Redirect back

    def test_upload_valid_xlsx_file(self, client):
        """Test upload with valid xlsx file."""
        # Create a simple xlsx content (just bytes for testing)
        data = {"file": (io.BytesIO(b"fake xlsx content"), "test.xlsx")}
        response = client.post(
            "/import/",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        # Should redirect to preview
        assert response.status_code == 302
        assert "/import/preview/" in response.location

    def test_preview_file_not_found(self, client):
        """Test preview with non-existent upload_id."""
        response = client.get("/import/preview/nonexistent-id", follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected back to upload page

    @patch("app.routes.import_log.ImporterFactory")
    def test_preview_parsing_error(self, mock_factory, client, app):
        """Test preview when parsing fails."""
        # First upload a file
        with app.app_context():
            from app.routes.import_log import UPLOAD_FOLDER

            upload_id = "test-error-id"
            filepath = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
            with open(filepath, "wb") as f:
                f.write(b"fake content")

            # Mock the importer to raise an error
            mock_importer = MagicMock()
            mock_importer.parse.side_effect = Exception("Parse error")
            mock_factory.get_importer.return_value = mock_importer

            response = client.get(f"/import/preview/{upload_id}", follow_redirects=True)

            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)

            assert response.status_code == 200

    @patch("app.routes.import_log.ImporterFactory")
    def test_preview_success(self, mock_factory, client, app):
        """Test preview with valid parsed data."""
        with app.app_context():
            from app.routes.import_log import UPLOAD_FOLDER

            upload_id = "test-preview-id"
            filepath = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
            with open(filepath, "wb") as f:
                f.write(b"fake content")

            # Mock successful parse
            mock_importer = MagicMock()
            mock_result = ImportResult(
                records=[
                    TimeEntryRecord(
                        date="2025-03-10",
                        entry_time="09:00",
                        exit_time="17:00",
                        observation=None,
                        is_valid=True,
                        error_message=None,
                    )
                ],
                total_records=1,
                valid_records=1,
                errors=[],
            )
            mock_importer.parse.return_value = mock_result
            mock_factory.get_importer.return_value = mock_importer

            response = client.get(f"/import/preview/{upload_id}")

            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)

            assert response.status_code == 200

    @patch("app.routes.import_log.ImporterFactory")
    def test_confirm_success(self, mock_factory, client, app):
        """Test confirm import with valid data."""
        with app.app_context():
            from app.routes.import_log import UPLOAD_FOLDER

            upload_id = "test-confirm-id"
            filepath = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
            with open(filepath, "wb") as f:
                f.write(b"fake content")

            # Mock successful parse
            mock_importer = MagicMock()
            mock_result = ImportResult(
                records=[
                    TimeEntryRecord(
                        date="2025-03-10",
                        entry_time="09:00",
                        exit_time="17:00",
                        observation="Note",
                        is_valid=True,
                        error_message=None,
                    )
                ],
                total_records=1,
                valid_records=1,
                errors=[],
            )
            mock_importer.parse.return_value = mock_result
            mock_factory.get_importer.return_value = mock_importer

            response = client.post(
                f"/import/confirm/{upload_id}", follow_redirects=False
            )

            assert response.status_code == 302
            # Should redirect to monthly log

    def test_confirm_file_not_found(self, client):
        """Test confirm with non-existent upload_id."""
        response = client.post("/import/confirm/nonexistent-id", follow_redirects=True)
        assert response.status_code == 200

    @patch("app.routes.import_log.ImporterFactory")
    def test_confirm_overwrites_existing_entry(self, mock_factory, client, app):
        """Test confirm overwrites existing schedule entry."""
        with app.app_context():
            from app.routes.import_log import UPLOAD_FOLDER

            # Create existing entry
            existing = ScheduleEntry(
                employee_id=1,
                date=date(2025, 3, 10),
                entries=[{"entry": "08:00", "exit": "16:00"}],
                absence_code=None,
            )
            db.session.add(existing)
            db.session.commit()

            upload_id = "test-overwrite-id"
            filepath = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
            with open(filepath, "wb") as f:
                f.write(b"fake content")

            mock_importer = MagicMock()
            mock_result = ImportResult(
                records=[
                    TimeEntryRecord(
                        date="2025-03-10",
                        entry_time="09:00",
                        exit_time="17:00",
                        observation="Updated",
                        is_valid=True,
                        error_message=None,
                    )
                ],
                total_records=1,
                valid_records=1,
                errors=[],
            )
            mock_importer.parse.return_value = mock_result
            mock_factory.get_importer.return_value = mock_importer

            response = client.post(
                f"/import/confirm/{upload_id}", follow_redirects=False
            )

            assert response.status_code == 302

            # Verify entry was updated
            entry = ScheduleEntry.query.filter_by(
                employee_id=1, date=date(2025, 3, 10)
            ).first()
            assert entry.entries[0]["entry"] == "09:00"
            assert entry.observation == "Updated"

    @patch("app.routes.import_log.ImporterFactory")
    def test_confirm_skips_invalid_records(self, mock_factory, client, app):
        """Test confirm skips invalid records."""
        with app.app_context():
            from app.routes.import_log import UPLOAD_FOLDER

            upload_id = "test-invalid-id"
            filepath = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
            with open(filepath, "wb") as f:
                f.write(b"fake content")

            mock_importer = MagicMock()
            mock_result = ImportResult(
                records=[
                    TimeEntryRecord(
                        date="2025-03-10",
                        entry_time="09:00",
                        exit_time="17:00",
                        observation=None,
                        is_valid=False,  # Invalid
                        error_message="Some error",
                    )
                ],
                total_records=1,
                valid_records=0,
                errors=[],
            )
            mock_importer.parse.return_value = mock_result
            mock_factory.get_importer.return_value = mock_importer

            response = client.post(
                f"/import/confirm/{upload_id}", follow_redirects=False
            )

            assert response.status_code == 302

    @patch("app.routes.import_log.ImporterFactory")
    def test_confirm_db_error(self, mock_factory, client, app, mocker):
        """Test confirm handles database errors."""
        with app.app_context():
            from app.routes.import_log import UPLOAD_FOLDER

            upload_id = "test-db-error-id"
            filepath = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
            with open(filepath, "wb") as f:
                f.write(b"fake content")

            mock_importer = MagicMock()
            mock_result = ImportResult(
                records=[
                    TimeEntryRecord(
                        date="2025-03-10",
                        entry_time="09:00",
                        exit_time="17:00",
                        observation=None,
                        is_valid=True,
                        error_message=None,
                    )
                ],
                total_records=1,
                valid_records=1,
                errors=[],
            )
            mock_importer.parse.return_value = mock_result
            mock_factory.get_importer.return_value = mock_importer

            # Mock commit to raise error
            mocker.patch.object(db.session, "commit", side_effect=Exception("DB Error"))

            response = client.post(
                f"/import/confirm/{upload_id}", follow_redirects=True
            )

            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)

            assert response.status_code == 200

    def test_cancel_removes_file(self, client, app):
        """Test cancel removes the uploaded file."""
        with app.app_context():
            from app.routes.import_log import UPLOAD_FOLDER

            upload_id = "test-cancel-id"
            filepath = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
            with open(filepath, "wb") as f:
                f.write(b"fake content")

            assert os.path.exists(filepath)

            response = client.post(
                f"/import/cancel/{upload_id}", follow_redirects=False
            )

            assert response.status_code == 302
            assert not os.path.exists(filepath)

    def test_cancel_nonexistent_file(self, client):
        """Test cancel with non-existent file doesn't error."""
        response = client.post("/import/cancel/nonexistent-id", follow_redirects=False)
        assert response.status_code == 302


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
