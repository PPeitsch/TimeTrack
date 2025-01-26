from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from models import Employee, ScheduleEntry
from utils.time_calculator import calculate_daily_hours

manual_entry = Blueprint("manual_entry", __name__)


@manual_entry.route("/entry", methods=["GET"])
def show_entry_form():
    return render_template("manual_entry.html")


@manual_entry.route("/entry", methods=["POST"])
def save_entry():
    data = request.json
    entries = []

    for entry in data["entries"]:
        if entry["entry"] and entry["exit"]:
            entries.append({"entry": entry["entry"], "exit": entry["exit"]})

    schedule_entry = ScheduleEntry(
        employee_id=data["employee_id"],
        date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
        entries=entries,
        absence_code=data.get("absence_code"),
    )

    db.session.add(schedule_entry)
    db.session.commit()

    return jsonify({"status": "success"})


@manual_entry.route("/entry/<date>", methods=["GET"])
def get_entry(date):
    entry = ScheduleEntry.query.filter_by(
        date=datetime.strptime(date, "%Y-%m-%d").date()
    ).first()

    return jsonify(entry.to_dict() if entry else {})
