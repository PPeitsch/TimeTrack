"""Endpoints for a monitor: ``/health`` and ``/ops/metrics``.

``/health`` is public and says only whether the app and its database answer, and which commit
runs. ``/ops/metrics`` gives counts (never hours, dates or notes) to whoever sends
``Authorization: Bearer <OPS_METRICS_TOKEN>``; without that setting it does not exist (404).
Both are exempt from the login guard (``PUBLIC_ENDPOINTS`` in ``app/auth.py``).
"""

import hmac
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, text

from app.auth import csrf
from app.db.database import db
from app.models.models import Employee, ScheduleEntry

ops_bp = Blueprint("ops", __name__)
csrf.exempt(ops_bp)


def git_version(root: Path) -> Optional[str]:
    """Short hash of the commit checked out in ``root``, read from ``.git``."""
    try:
        head = (root / ".git" / "HEAD").read_text().strip()
        if head.startswith("ref: "):
            ref = head[5:]
            loose = root / ".git" / ref
            if loose.exists():
                return loose.read_text().strip()[:7]
            for line in (root / ".git" / "packed-refs").read_text().splitlines():
                if line.endswith(" " + ref):
                    return line.split()[0][:7]
            return None
        return head[:7]
    except OSError:
        return None


@ops_bp.route("/health")
def health():
    """``ok`` and the version, or 503 when the database does not answer."""
    version = git_version(Path(current_app.root_path).parent)
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any database failure means "not healthy"
        current_app.logger.exception("health: the database does not answer")
        return jsonify(status="error", version=version), 503
    return jsonify(status="ok", version=version)


def _authorized() -> Optional[bool]:
    """None when the endpoint is off; otherwise whether the request carries the token."""
    expected = current_app.config.get("OPS_METRICS_TOKEN")
    if not expected:
        return None
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    return scheme.lower() == "bearer" and hmac.compare_digest(
        token.encode(), expected.encode()
    )


def collect(today: date) -> list:
    """Days logged in the last week (worked and absences), in total, and users."""
    week = today - timedelta(days=7)
    recent = db.session.query(ScheduleEntry).filter(ScheduleEntry.date > week)
    absences = recent.filter(ScheduleEntry.absence_code.isnot(None)).count()
    total_recent = recent.count()
    return [
        {
            "name": "days_logged_7d",
            "value": total_recent - absences,
            "labels": {"kind": "work"},
        },
        {"name": "days_logged_7d", "value": absences, "labels": {"kind": "absence"}},
        {
            "name": "days_logged_total",
            "value": db.session.query(func.count(ScheduleEntry.id)).scalar(),
        },
        {"name": "users", "value": db.session.query(func.count(Employee.id)).scalar()},
    ]


@ops_bp.route("/ops/metrics")
def metrics():
    """The counts, for whoever carries the token."""
    allowed = _authorized()
    if allowed is None:
        return jsonify(error="not found"), 404
    if not allowed:
        response = jsonify(error="invalid or missing token")
        response.headers["WWW-Authenticate"] = "Bearer"
        return response, 401
    return jsonify(metrics=collect(date.today()))
