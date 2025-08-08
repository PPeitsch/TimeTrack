from datetime import datetime
from typing import Any, Dict, Optional, cast

from flask import Blueprint, jsonify, render_template, request

from app.db.database import db
from app.models.models import AbsenceCode, Employee, ScheduleEntry
from app.utils.time_calculator import calculate_daily_hours
from app.utils.validators import validate_date, validate_entries

manual_entry = Blueprint("manual_entry", __name__)


@manual_entry.route("/entry", methods=["GET"])
def show_entry_form():
    employees = Employee.query.all()
    # Fetch codes dynamically from the database
    absence_codes = AbsenceCode.query.order_by(AbsenceCode.code).all()
    return render_template(
        "manual_entry.html", employees=employees, absence_codes=absence_codes
    )


@manual_entry.route("/entry", methods=["POST"])
def save_entry():
    data = request.json
    if data is None:
        return jsonify({"error": "No JSON data provided"}), 400

    date_str = data.get("date")
    if date_str is None:
        return jsonify({"error": "Date is required"}), 400

    if not validate_date(date_str):
        return jsonify({"error": "Invalid date format"}), 400

    absence_code = data.get("absence_code")

    if absence_code is None:
        entries = data.get("entries")
        if entries is None:
            return jsonify({"error": "Entries are required for work day"}), 400
        if not entries:
            return jsonify({"error": "No time entries provided for work day"}), 400
        is_valid, error = validate_entries(entries)
        if not is_valid:
            return jsonify({"error": error}), 400

    entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    employee_id = data.get("employee_id")
    if employee_id is None:
        return jsonify({"error": "Employee ID is required"}), 400

    existing_entry = ScheduleEntry.query.filter_by(
        employee_id=employee_id, date=entry_date
    ).first()

    entries = data.get("entries", [])

    if existing_entry:
        existing_entry.entries = [] if absence_code else entries
        existing_entry.absence_code = absence_code
        db.session.commit()
    else:
        schedule_entry = ScheduleEntry(
            employee_id=employee_id,
            date=entry_date,
            entries=[] if absence_code else entries,
            absence_code=absence_code,
        )
        db.session.add(schedule_entry)
        db.session.commit()

    if absence_code is None:
        hours = calculate_daily_hours(entries)
        return jsonify({"status": "success", "hours": hours})

    return jsonify({"status": "success"})


@manual_entry.route("/entry/<date>", methods=["GET"])
def get_entry(date):
    if not validate_date(date):
        return jsonify({"error": "Invalid date format"}), 400

    entry = ScheduleEntry.query.filter_by(
        date=datetime.strptime(date, "%Y-%m-%d").date(),
        employee_id=1,
    ).first()

    if entry:
        return jsonify(
            {
                "entries": entry.entries,
                "absence_code": entry.absence_code,
                "hours": (
                    calculate_daily_hours(entry.entries)
                    if not entry.absence_code
                    else 0
                ),
            }
        )

    return jsonify({})
