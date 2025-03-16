from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from app.db.database import db
from app.models.models import AbsenceCode, Employee, ScheduleEntry
from app.utils.time_calculator import calculate_daily_hours
from app.utils.validators import validate_date, validate_entries

manual_entry = Blueprint("manual_entry", __name__)


@manual_entry.route("/entry", methods=["GET"])
def show_entry_form():
    employees = Employee.query.all()
    absence_codes = AbsenceCode.query.all()
    return render_template(
        "manual_entry.html", employees=employees, absence_codes=absence_codes
    )


@manual_entry.route("/entry", methods=["POST"])
def save_entry():
    data = request.json

    if not validate_date(data["date"]):
        return jsonify({"error": "Invalid date format"}), 400

    # Only validate entries if there's no absence code
    if not data.get("absence_code") and data["entries"]:
        is_valid, error = validate_entries(data["entries"])
        if not is_valid:
            return jsonify({"error": error}), 400

    # Check if an entry already exists for this date and employee
    existing_entry = ScheduleEntry.query.filter_by(
        employee_id=data["employee_id"],
        date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
    ).first()

    if existing_entry:
        # Update existing entry
        existing_entry.entries = data["entries"] if not data.get("absence_code") else []
        existing_entry.absence_code = data.get("absence_code")
        db.session.commit()
    else:
        # Create new entry
        schedule_entry = ScheduleEntry(
            employee_id=data["employee_id"],
            date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
            entries=data["entries"] if not data.get("absence_code") else [],
            absence_code=data.get("absence_code"),
        )
        db.session.add(schedule_entry)
        db.session.commit()

    # Calculate hours if not an absence
    if not data.get("absence_code"):
        hours = calculate_daily_hours(data["entries"])
        return jsonify({"status": "success", "hours": hours})

    return jsonify({"status": "success"})


@manual_entry.route("/entry/<date>", methods=["GET"])
def get_entry(date):
    if not validate_date(date):
        return jsonify({"error": "Invalid date format"}), 400

    entry = ScheduleEntry.query.filter_by(
        date=datetime.strptime(date, "%Y-%m-%d").date(),
        employee_id=1,  # Default employee ID until login is implemented
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


@manual_entry.route("/entry/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    entry = ScheduleEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"status": "success", "message": "Entry deleted successfully"})
