from calendar import monthrange
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from app.models.models import ScheduleEntry
from app.utils.time_calculator import calculate_daily_hours

time_log = Blueprint("time_log", __name__, url_prefix="/logs")


@time_log.route("/", methods=["GET"])
def show_logs():
    return render_template("time_log.html")


@time_log.route("/monthly/<int:year>/<int:month>", methods=["GET"])
def get_monthly_logs(year, month):
    try:
        # Get start and end dates for the month
        start_date = datetime(year, month, 1).date()
        _, days_in_month = monthrange(year, month)
        end_date = datetime(year, month, days_in_month).date()

        # Get entries for the month
        entries = (
            ScheduleEntry.query.filter(
                ScheduleEntry.date.between(start_date, end_date),
                ScheduleEntry.employee_id == 1,  # Default employee ID
            )
            .order_by(ScheduleEntry.date)
            .all()
        )

        # Format entries for display
        formatted_entries = []
        for entry in entries:
            if entry.absence_code:
                # If it's an absence day
                formatted_entries.append(
                    {
                        "date": entry.date.strftime("%Y-%m-%d"),
                        "type": entry.absence_code,
                        "entries": [],
                        "total_hours": 0,
                    }
                )
            else:
                # If it's a regular work day
                hours = calculate_daily_hours(entry.entries)
                formatted_entries.append(
                    {
                        "date": entry.date.strftime("%Y-%m-%d"),
                        "type": "Work Day",
                        "entries": entry.entries,
                        "total_hours": hours,
                    }
                )

        return jsonify(formatted_entries)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
