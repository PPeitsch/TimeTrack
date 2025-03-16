from calendar import monthrange
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from app.models.models import ScheduleEntry
from app.utils.time_calculator import (
    calculate_daily_hours,
    calculate_monthly_hours,
    calculate_weekly_hours,
)

time_summary = Blueprint("time_summary", __name__, url_prefix="/summary")


@time_summary.route("/", methods=["GET"])
def show_summary():
    return render_template("time_summary.html")


@time_summary.route("/daily/<date>", methods=["GET"])
def get_daily_summary(date):
    try:
        # Parse the date string to a datetime object
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        # Get entry for the date
        entry = ScheduleEntry.query.filter_by(
            date=date_obj,
            employee_id=1,  # Default employee ID until login is implemented
        ).first()

        # Check if it's a weekend
        is_weekend = date_obj.weekday() >= 5  # 5 is Saturday, 6 is Sunday
        required_hours = 0 if is_weekend else 8

        if not entry:
            return jsonify(
                {
                    "hours": 0,
                    "required": required_hours,
                    "difference": -required_hours if not is_weekend else 0,
                    "absence_code": None,
                }
            )

        # If it's an absence day, required hours is 0
        if entry.absence_code:
            required_hours = 0

        # Calculate hours if not an absence
        hours = calculate_daily_hours(entry.entries) if not entry.absence_code else 0

        return jsonify(
            {
                "hours": hours,
                "required": required_hours,
                "difference": hours - required_hours,
                "absence_code": entry.absence_code,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@time_summary.route("/monthly/<int:year>/<int:month>", methods=["GET"])
def get_monthly_summary(year, month):
    try:
        # Get start and end dates for the month
        start_date = datetime(year, month, 1).date()
        _, days_in_month = monthrange(year, month)
        end_date = datetime(year, month, days_in_month).date()

        # Get entries for the month
        entries = ScheduleEntry.query.filter(
            ScheduleEntry.date.between(start_date, end_date),
            ScheduleEntry.employee_id == 1,  # Default employee ID
        ).all()

        # Calculate monthly hours
        monthly_data = calculate_monthly_hours(entries)

        return jsonify(monthly_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
