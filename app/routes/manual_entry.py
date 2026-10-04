from datetime import datetime

from flask import Blueprint, jsonify, redirect, request, url_for
from flask_babel import gettext as _

from app.auth import current_employee_id
from app.db.database import db
from app.models.models import AbsenceCode, ScheduleEntry
from app.utils.time_calculator import calculate_daily_hours
from app.utils.validators import validate_date, validate_entries

manual_entry = Blueprint("manual_entry", __name__)


@manual_entry.route("/entry", methods=["GET"])
def show_entry_form():
    """Old manual entry URL; days are edited from the calendar."""
    return redirect(url_for("main.calendar"), code=301)


@manual_entry.route("/entry", methods=["POST"])
def save_entry():
    data = request.json
    if data is None:
        return jsonify({"error": _("No JSON data provided")}), 400

    date_str = data.get("date")
    if date_str is None:
        return jsonify({"error": _("Date is required")}), 400

    if not validate_date(date_str):
        return jsonify({"error": _("Invalid date format")}), 400

    absence_code = data.get("absence_code")
    if absence_code is not None and not (
        AbsenceCode.query.filter_by(code=absence_code).first()
    ):
        return jsonify({"error": _("Unknown absence code")}), 400

    if absence_code is None:
        entries = data.get("entries")
        if entries is None:
            return jsonify({"error": _("Entries are required for work day")}), 400
        if not entries:
            return jsonify({"error": _("No time entries provided for work day")}), 400
        is_valid, error = validate_entries(entries)
        if not is_valid:
            return jsonify({"error": error}), 400

    entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    # The employee is the logged-in user; never trust an id sent by the client.
    employee_id = current_employee_id()

    existing_entry = ScheduleEntry.query.filter_by(
        employee_id=employee_id, date=entry_date
    ).first()

    entries = data.get("entries", [])

    if existing_entry is None:
        existing_entry = ScheduleEntry(employee_id=employee_id, date=entry_date)
        db.session.add(existing_entry)
    existing_entry.entries = [] if absence_code else entries
    existing_entry.absence_code = absence_code
    # A request without the key keeps the note already saved for the day.
    if "observation" in data:
        existing_entry.observation = (data["observation"] or "").strip() or None
    db.session.commit()

    if absence_code is None:
        hours = calculate_daily_hours(entries)
        return jsonify({"status": "success", "hours": hours})

    return jsonify({"status": "success"})


@manual_entry.route("/entry/<date>", methods=["GET"])
def get_entry(date):
    if not validate_date(date):
        return jsonify({"error": _("Invalid date format")}), 400

    entry = ScheduleEntry.query.filter_by(
        date=datetime.strptime(date, "%Y-%m-%d").date(),
        employee_id=current_employee_id(),
    ).first()

    if entry:
        return jsonify(
            {
                "entries": entry.entries,
                "absence_code": entry.absence_code,
                "observation": entry.observation,
                "hours": (
                    calculate_daily_hours(entry.entries)
                    if not entry.absence_code
                    else 0
                ),
            }
        )

    return jsonify({})
