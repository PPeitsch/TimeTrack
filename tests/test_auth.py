"""Tests for login, logout, CSRF and the global login guard."""

import pytest

from app import create_app
from app.auth import _failed_logins, set_credentials
from app.config.config import Config
from app.db.database import db
from app.models.models import Employee


class AuthConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    HOLIDAY_AUTO_FETCH = False
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False
    LOGIN_MAX_ATTEMPTS = 3


@pytest.fixture
def auth_app():
    app = create_app(AuthConfig)
    with app.app_context():
        db.create_all()
        set_credentials("admin", "s3cret")
        yield app
        db.session.remove()
        db.drop_all()
    _failed_logins.clear()


@pytest.fixture
def auth_client(auth_app):
    return auth_app.test_client()


def login(client, username="admin", password="s3cret", **kwargs):
    return client.post(
        "/login", data={"username": username, "password": password}, **kwargs
    )


class TestLoginGuard:
    def test_pages_redirect_to_login(self, auth_client):
        response = auth_client.get("/summary/")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_api_returns_401_json(self, auth_client):
        response = auth_client.get("/settings/api/absence-codes")
        assert response.status_code == 401
        assert response.get_json() == {"error": "Authentication required"}

    def test_static_and_login_are_public(self, auth_client):
        assert auth_client.get("/login").status_code == 200
        assert auth_client.get("/static/js/utils.js").status_code == 200


class TestLogin:
    def test_valid_credentials_log_in(self, auth_client):
        response = login(auth_client)
        assert response.status_code == 302
        assert auth_client.get("/summary/").status_code == 200

    def test_invalid_password_is_rejected(self, auth_client):
        response = login(auth_client, password="wrong")
        assert response.status_code == 401
        assert auth_client.get("/summary/").status_code == 302

    def test_next_redirects_only_inside_the_app(self, auth_client):
        response = login(auth_client, query_string={"next": "/summary/"})
        assert response.headers["Location"].endswith("/summary/")

        auth_client.post("/logout")
        response = login(auth_client, query_string={"next": "https://evil.example"})
        assert "evil.example" not in response.headers["Location"]

    def test_rate_limit_after_repeated_failures(self, auth_client):
        for _ in range(3):
            login(auth_client, password="wrong")
        response = login(auth_client)
        assert response.status_code == 429

    def test_logout_ends_session(self, auth_client):
        login(auth_client)
        auth_client.post("/logout")
        assert auth_client.get("/summary/").status_code == 302

    def test_demo_mode_shows_credentials(self, auth_app):
        auth_app.config.update(DEMO_MODE=True, DEMO_USERNAME="demo")
        html = auth_app.test_client().get("/login").get_data(as_text=True)
        assert "This is a demo" in html


class TestCredentials:
    def test_password_is_hashed(self, auth_app):
        employee = db.session.get(Employee, 1)
        assert employee.username == "admin"
        assert employee.password_hash != "s3cret"
        assert employee.check_password("s3cret")

    def test_cli_set_password(self, auth_app):
        runner = auth_app.test_cli_runner()
        result = runner.invoke(
            args=["user", "set-password", "pablo"], input="nueva\nnueva\n"
        )
        assert result.exit_code == 0, result.output
        employee = db.session.get(Employee, 1)
        assert employee.username == "pablo"
        assert employee.check_password("nueva")


def test_csrf_is_enforced():
    class CsrfConfig(AuthConfig):
        WTF_CSRF_ENABLED = True

    app = create_app(CsrfConfig)
    with app.app_context():
        db.create_all()
        set_credentials("admin", "s3cret")
        client = app.test_client()
        response = login(client)
        assert response.status_code == 400
        db.drop_all()
