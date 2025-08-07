from calendar import monthrange
from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template

from app.models.models import Holiday, ScheduleEntry

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
            entry = entries_map.get(current_date)

            if entry and entry.absence_code:
                day_type = entry.absence_code
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
