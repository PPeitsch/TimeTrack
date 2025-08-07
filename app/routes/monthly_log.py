from calendar import monthrange
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from app.db.database import db
from app.models.models import AbsenceCode, Holiday, ScheduleEntry

monthly_log_bp = Blueprint("monthly_log", __name__, url_prefix="/monthly-log")


@monthly_log_bp.route("/", methods=["GET"])
def view_monthly_log():
    """Renders the main calendar view page."""
    return render_template("monthly_log.html")


@monthly_log_bp.route("/api/absence-codes", methods=["GET"])
def get_absence_codes():
    """Returns a list of available absence codes."""
    try:
        codes = AbsenceCode.query.all()
        return jsonify([code.code for code in codes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@monthly_log_bp.route("/api/<int:year>/<int:month>", methods=["GET"])
def get_monthly_log_data(year, month):
    """
    Provides the data for all days in a given month for the calendar view.
    """
    try:
        start_date = date(year, month, 1)
        days_in_month = monthrange(year, month)[1]
        end_date = date(year, month, days_in_month)

        entries_query = ScheduleEntry.query.filter(
            ScheduleEntry.date.between(start_date, end_date),
            ScheduleEntry.employee_id == 1,
        ).all()
        entries_map = {entry.date: entry for entry in entries_query}

        holidays_query = Holiday.query.filter(
            Holiday.date.between(start_date, end_date)
        ).all()
        holidays_set = {h.date for h in holidays_query}

        days_data = []
        current_date = start_date
        while current_date <= end_date:
            day_type = "Work Day"
            # Logic precedence: An explicit entry overrides holidays and weekends.
            entry = entries_map.get(current_date)
            if entry:
                day_type = entry.absence_code or "Work Day"
            elif current_date in holidays_set:
                day_type = "Holiday"
            elif current_date.weekday() >= 5:
                day_type = "Weekend"

            days_data.append(
                {
                    "date": current_date.isoformat(),
                    "type": day_type,
                }
            )
            current_date += timedelta(days=1)

        return jsonify(days_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@monthly_log_bp.route("/api/update-days", methods=["POST"])
def update_day_types():
    """
    Updates the type for a list of dates.
    "Work Day" is treated as the default, which means deleting any existing override.
    """
    data = request.json
    if not data or "dates" not in data or "day_type" not in data:
        return jsonify({"error": "Invalid request body"}), 400

    dates_to_update = [datetime.strptime(d, "%Y-%m-%d").date() for d in data["dates"]]
    new_day_type = data["day_type"]

    try:
        for entry_date in dates_to_update:
            existing_entry = ScheduleEntry.query.filter_by(
                employee_id=1, date=entry_date
            ).first()

            if new_day_type == "Work Day":
                # If reverting to Work Day, delete the override entry if it exists.
                if existing_entry:
                    db.session.delete(existing_entry)
            else:
                # If setting an absence, create or update the entry.
                if existing_entry:
                    existing_entry.absence_code = new_day_type
                    existing_entry.entries = []  # Ensure entries are cleared
                else:
                    new_entry = ScheduleEntry(
                        employee_id=1,
                        date=entry_date,
                        entries=[],
                        absence_code=new_day_type,
                    )
                    db.session.add(new_entry)

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
