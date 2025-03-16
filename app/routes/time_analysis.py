from calendar import monthrange
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from app.models.models import ScheduleEntry
from app.utils.time_calculator import (
    calculate_daily_hours,
    calculate_monthly_hours,
    calculate_weekly_hours,
)

time_analysis = Blueprint("time_analysis", __name__)


@time_analysis.route("/analysis", methods=["GET"])
def show_analysis():
    return render_template("time_analysis.html")


@time_analysis.route("/analysis/daily/<date>", methods=["GET"])
def get_daily_analysis(date):
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
                    "difference": -required_hours,
                    "absence_code": None,
                }
            )

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


@time_analysis.route("/analysis/weekly/<date>", methods=["GET"])
def get_weekly_analysis(date):
    try:
        # Parse the date
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        # Get the start of the week (Monday)
        start_date = date_obj - timedelta(days=date_obj.weekday())
        end_date = start_date + timedelta(days=6)

        # Get entries for the week
        entries = ScheduleEntry.query.filter(
            ScheduleEntry.date.between(start_date, end_date),
            ScheduleEntry.employee_id == 1,  # Default employee ID
        ).all()

        # Calculate weekly hours
        weekly_data = calculate_weekly_hours(entries)

        return jsonify(weekly_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@time_analysis.route("/analysis/monthly/<int:year>/<int:month>", methods=["GET"])
def get_monthly_analysis(year, month):
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
