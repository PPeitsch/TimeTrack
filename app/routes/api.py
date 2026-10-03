"""JSON API used by the calendar screen."""

from calendar import monthrange
from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_babel import gettext as _

from app.auth import current_employee_id
from app.db.database import db
from app.models.models import AbsenceCode, ScheduleEntry
from app.services.calendar_service import DayInfo, resolve_day, resolve_days, summarize
from app.utils.validators import validate_entries

api_bp = Blueprint("api", __name__, url_prefix="/api")

KINDS = ("work", "absence", "default")


def serialize_day(day: DayInfo) -> dict:
    return {
        "date": day.date.isoformat(),
        "type": day.type,
        "base_type": day.base_type,
        "entries": day.entries,
        "worked": day.worked,
        "required": day.required,
        "difference": day.difference,
        "absence_code": day.absence_code,
        "observation": day.observation,
        "has_entry": day.has_entry,
    }


@api_bp.route("/days/<int:year>/<int:month>", methods=["GET"])
def month_days(year, month):
    try:
        start = date(year, month, 1)
    except ValueError:
        return jsonify({"error": _("Invalid month")}), 400
    end = date(year, month, monthrange(year, month)[1])
    days = resolve_days(current_employee_id(), start, end)
    return jsonify(
        {"days": [serialize_day(d) for d in days], "summary": summarize(days)}
    )


@api_bp.route("/days/<day_str>", methods=["PUT"])
def save_day(day_str):
    """Save one day.

    Body: {"kind": "work" | "absence" | "default", "entries": [...],
           "absence_code": str, "observation": str}
    "default" removes the override but keeps the observation, if any.
    """
    try:
        day = datetime.strptime(day_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": _("Invalid date format")}), 400

    data = request.get_json(silent=True) or {}
    kind = data.get("kind")
    if kind not in KINDS:
        return jsonify({"error": _("kind must be one of: work, absence, default")}), 400

    observation = (data.get("observation") or "").strip() or None
    entries = data.get("entries") or []
    absence_code = data.get("absence_code")

    if kind == "work" and entries:
        is_valid, error = validate_entries(entries)
        if not is_valid:
            return jsonify({"error": error}), 400
    if kind == "absence" and not (
        absence_code and AbsenceCode.query.filter_by(code=absence_code).first()
    ):
        return jsonify({"error": _("Unknown absence code")}), 400

    employee_id = current_employee_id()
    entry = ScheduleEntry.query.filter_by(employee_id=employee_id, date=day).first()

    try:
        if kind == "default" and not observation:
            if entry is not None:
                db.session.delete(entry)
        else:
            if entry is None:
                entry = ScheduleEntry(employee_id=employee_id, date=day, entries=[])
                db.session.add(entry)
            entry.observation = observation
            if kind == "work":
                entry.absence_code = None
                entry.entries = [
                    {"entry": e["entry"], "exit": e["exit"]} for e in entries
                ]
            elif kind == "absence":
                entry.absence_code = absence_code
                entry.entries = []
            else:  # default with an observation: keep only the note
                entry.absence_code = None
                entry.entries = []
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500

    return jsonify(serialize_day(resolve_day(employee_id, day)))
