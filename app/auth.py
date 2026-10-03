"""Authentication for the single TimeTrack user.

TimeTrack is single-user: there is one account (the Employee with id 1), created
with `flask user set-password`. With DEMO_MODE enabled the login page shows the
demo credentials so visitors can try the app.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, cast
from urllib.parse import urlsplit

import click
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_babel import gettext as _
from flask_login import (  # type: ignore
    LoginManager,
    current_user,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect  # type: ignore

from app.db.database import db
from app.models.models import Employee

DEFAULT_EMPLOYEE_ID = 1

login_manager = LoginManager()
csrf = CSRFProtect()
auth_bp = Blueprint("auth", __name__)

# Endpoints reachable without a session.
PUBLIC_ENDPOINTS = {"auth.login", "static", "i18n.set_language"}

# Failed login attempts per client IP, kept in memory (single process is enough
# for a self-hosted single-user app).
_failed_logins: Dict[str, Deque[float]] = defaultdict(deque)


@login_manager.user_loader
def load_user(user_id: str) -> Optional[Employee]:
    return cast(Optional[Employee], db.session.get(Employee, int(user_id)))


def current_employee_id() -> int:
    """Id of the employee whose data the request works on.

    Falls back to the default employee when login is disabled (tests).
    """
    if current_user and current_user.is_authenticated:
        return int(current_user.id)
    return DEFAULT_EMPLOYEE_ID


def require_login():
    """Global guard registered with app.before_request."""
    if current_app.config.get("LOGIN_DISABLED"):
        return None
    if request.endpoint in PUBLIC_ENDPOINTS or current_user.is_authenticated:
        return None
    if _wants_json():
        return jsonify({"error": "Authentication required"}), 401
    return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))


def _wants_json() -> bool:
    if request.is_json or "/api/" in request.path:
        return True
    best = request.accept_mimetypes.best_match(["text/html", "application/json"])
    return best == "application/json"


def _safe_next(target: Optional[str]) -> str:
    """Only allow relative redirects back into the app."""
    if target:
        parts = urlsplit(target)
        if not parts.scheme and not parts.netloc and target.startswith("/"):
            return target
    return url_for("main.index")


def _too_many_attempts(ip: str) -> bool:
    window = current_app.config["LOGIN_RATE_WINDOW_SECONDS"]
    attempts = _failed_logins[ip]
    now = time.monotonic()
    while attempts and now - attempts[0] > window:
        attempts.popleft()
    return len(attempts) >= int(current_app.config["LOGIN_MAX_ATTEMPTS"])


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    demo = current_app.config.get("DEMO_MODE")
    context = {
        "demo_username": current_app.config.get("DEMO_USERNAME") if demo else None,
        "demo_password": current_app.config.get("DEMO_PASSWORD") if demo else None,
    }

    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if _too_many_attempts(ip):
            flash(_("Too many failed attempts. Try again in a few minutes."), "error")
            return render_template("login.html", **context), 429

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = Employee.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            _failed_logins[ip].append(time.monotonic())
            flash(_("Invalid username or password."), "error")
            return render_template("login.html", username=username, **context), 401

        _failed_logins.pop(ip, None)
        login_user(user, remember=bool(request.form.get("remember")))
        return redirect(_safe_next(request.args.get("next")))

    return render_template("login.html", **context)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash(_("You have been logged out."), "success")
    return redirect(url_for("auth.login"))


@click.group("user")
def user_cli():
    """Manage the TimeTrack login."""


@user_cli.command("set-password")
@click.argument("username")
@click.password_option()
def set_password_command(username: str, password: str) -> None:
    """Set the username and password of the single TimeTrack user."""
    set_credentials(username, password)
    click.echo(f"Login updated for user '{username}'.")


def set_credentials(username: str, password: str) -> Employee:
    """Create or update the default employee with the given login."""
    username = username.strip()
    if not username or not password:
        raise ValueError("Username and password are required.")
    employee = cast(Optional[Employee], db.session.get(Employee, DEFAULT_EMPLOYEE_ID))
    if employee is None:
        employee = Employee(id=DEFAULT_EMPLOYEE_ID, name=username)
        db.session.add(employee)
    employee.username = username  # type: ignore[assignment]
    employee.set_password(password)
    db.session.commit()
    return employee


def init_auth(app) -> None:
    login_manager.init_app(app)
    csrf.init_app(app)
    app.register_blueprint(auth_bp)
    app.before_request(require_login)
    app.cli.add_command(user_cli)
