"""Tests for the security hardening: config guards, upload ids, input validation."""

import os
import uuid

import pytest

from app import create_app
from app.config.config import Config
from app.routes.import_log import UPLOAD_FOLDER, _get_filepath


class ProductionConfig(Config):
    SECRET_KEY = None
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    HOLIDAY_AUTO_FETCH = False


def test_create_app_requires_secret_key_outside_debug(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(ProductionConfig)


def test_create_app_generates_key_when_testing():
    class TestingConfig(ProductionConfig):
        TESTING = True

    app = create_app(TestingConfig)
    assert app.config["SECRET_KEY"]


class TestUploadIds:
    def test_rejects_non_uuid(self):
        assert _get_filepath("a") is None
        assert _get_filepath("../etc/passwd") is None

    def test_rejects_prefix_match(self):
        upload_id = str(uuid.uuid4())
        path = os.path.join(UPLOAD_FOLDER, f"{upload_id}.xlsx")
        open(path, "wb").close()
        try:
            assert _get_filepath(upload_id[:8]) is None
            assert _get_filepath(upload_id) == path
        finally:
            os.remove(path)

    def test_preview_with_invalid_id_redirects(self, client):
        response = client.get("/import/preview/not-a-uuid")
        assert response.status_code == 302


class TestUpdateDaysValidation:
    def test_unknown_day_type_is_rejected(self, client, default_employee_id):
        payload = {"dates": ["2025-09-01"], "day_type": "<img src=x onerror=alert(1)>"}
        response = client.post("/monthly-log/api/update-days", json=payload)
        assert response.status_code == 400

    def test_malformed_date_is_rejected(self, client, default_employee_id):
        payload = {"dates": ["2025-13-45"], "day_type": "Work Day"}
        response = client.post("/monthly-log/api/update-days", json=payload)
        assert response.status_code == 400
