"""Tests for /health and /ops/metrics, the endpoints for a monitor."""

from datetime import date, timedelta

import pytest

from app import create_app
from app.config.config import Config
from app.db.database import db
from app.models.models import Employee, ScheduleEntry
from app.routes.ops import git_version


class GuardedConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    HOLIDAY_AUTO_FETCH = False
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False
    OPS_METRICS_TOKEN = "s3cret"


@pytest.fixture
def guarded():
    """An app with the login guard on and a metrics token."""
    app = create_app(GuardedConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_health_needs_no_login(guarded):
    response = guarded.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_metrics_needs_the_token(guarded):
    client = guarded.test_client()
    assert client.get("/ops/metrics").status_code == 401
    bad = client.get("/ops/metrics", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401


def test_metrics_is_off_without_a_token(app):
    assert app.config.get("OPS_METRICS_TOKEN") is None
    assert app.test_client().get("/ops/metrics").status_code == 404


def test_metrics_counts(guarded):
    employee = Employee(name="a")
    db.session.add(employee)
    db.session.commit()
    today = date.today()
    db.session.add_all(
        [
            ScheduleEntry(employee_id=employee.id, date=today, entries=[]),
            ScheduleEntry(
                employee_id=employee.id,
                date=today - timedelta(days=1),
                entries=[],
                absence_code="LIC",
            ),
            ScheduleEntry(
                employee_id=employee.id, date=today - timedelta(days=40), entries=[]
            ),
        ]
    )
    db.session.commit()
    response = guarded.test_client().get(
        "/ops/metrics", headers={"Authorization": "Bearer s3cret"}
    )
    assert response.status_code == 200
    values = {
        (m["name"], tuple(sorted((m.get("labels") or {}).items()))): m["value"]
        for m in response.get_json()["metrics"]
    }
    assert values[("days_logged_7d", (("kind", "work"),))] == 1
    assert values[("days_logged_7d", (("kind", "absence"),))] == 1
    assert values[("days_logged_total", ())] == 3
    assert values[("users", ())] == 1


def test_git_version(tmp_path):
    git = tmp_path / ".git"
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/main\n")
    (git / "refs" / "heads" / "main").write_text("0123456789abcdef\n")
    assert git_version(tmp_path) == "0123456"
    (git / "refs" / "heads" / "main").unlink()
    (git / "packed-refs").write_text("fedcba9876543210 refs/heads/main\n")
    assert git_version(tmp_path) == "fedcba9"
    assert git_version(tmp_path / "missing") is None


def test_health_is_503_when_the_database_fails(guarded, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("database down")

    monkeypatch.setattr(db.session, "execute", broken)
    response = guarded.test_client().get("/health")
    assert response.status_code == 503
    assert response.get_json()["status"] == "error"


def test_git_version_detached_and_unknown_ref(tmp_path):
    git = tmp_path / ".git"
    git.mkdir()
    (git / "HEAD").write_text("abcdef0123456789\n")
    assert git_version(tmp_path) == "abcdef0"
    (git / "HEAD").write_text("ref: refs/heads/other\n")
    (git / "packed-refs").write_text("fedcba9876543210 refs/heads/main\n")
    assert git_version(tmp_path) is None
