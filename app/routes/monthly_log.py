from calendar import monthrange
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request

from app.auth import current_employee_id
from app.db.database import db
from app.models.models import AbsenceCode, Holiday, ScheduleEntry

monthly_log_bp = Blueprint("monthly_log", __name__, url_prefix="/monthly-log")


@monthly_log_bp.route("/", methods=["GET"])
def view_monthly_log():
    """Renders the main calendar view page."""
    return render_template("monthly_log.html")


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
            ScheduleEntry.employee_id == current_employee_id(),
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
            entry = entries_map.get(current_date)

            if entry is not None:
                # An explicit entry exists, it takes highest precedence.
                # If absence_code is None, it's an explicit "Work Day".
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

    except Exception:
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error"}), 500


@monthly_log_bp.route("/api/update-days", methods=["POST"])
def update_day_types():
    """
    Updates the type for a list of dates.
    Handles a special "DEFAULT" type to revert to the base calendar state.
    """
    data = request.json
    if not data or "dates" not in data or "day_type" not in data:
        return jsonify({"error": "Invalid request body"}), 400

    try:
        dates_to_update = [
            datetime.strptime(d, "%Y-%m-%d").date() for d in data["dates"]
        ]
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid date format"}), 400

    new_day_type = data["day_type"]
    if new_day_type not in ("DEFAULT", "Work Day") and not (
        AbsenceCode.query.filter_by(code=new_day_type).first()
    ):
        return jsonify({"error": "Unknown day type"}), 400

    try:
        if new_day_type == "DEFAULT":
            # Revert to default by deleting the override entry.
            ScheduleEntry.query.filter(
                ScheduleEntry.employee_id == current_employee_id(),
                ScheduleEntry.date.in_(dates_to_update),
            ).delete(synchronize_session=False)
        else:
            # For any other type, create or update entries.
            new_absence_code = None if new_day_type == "Work Day" else new_day_type
            for entry_date in dates_to_update:
                existing_entry = ScheduleEntry.query.filter_by(
                    employee_id=current_employee_id(), date=entry_date
                ).first()

                if existing_entry:
                    existing_entry.absence_code = new_absence_code
                    if new_absence_code:
                        existing_entry.entries = []
                else:
                    new_entry = ScheduleEntry(
                        employee_id=current_employee_id(),
                        date=entry_date,
                        entries=[],
                        absence_code=new_absence_code,
                    )
                    db.session.add(new_entry)

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error"}), 500
