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
    entry = ScheduleEntry.query.filter_by(
        date=datetime.strptime(date, "%Y-%m-%d").date()
    ).first()

    if not entry:
        return jsonify({"hours": 0, "required": 8, "difference": -8})

    hours = calculate_daily_hours(entry.entries) if not entry.absence_code else 0

    return jsonify({"hours": hours, "required": 8, "difference": hours - 8})


@time_analysis.route("/analysis/weekly/<date>", methods=["GET"])
def get_weekly_analysis(date):
    start_date = datetime.strptime(date, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=6)

    entries = ScheduleEntry.query.filter(
        ScheduleEntry.date.between(start_date, end_date)
    ).all()

    return jsonify(calculate_weekly_hours(entries))


@time_analysis.route("/analysis/monthly/<year>/<month>", methods=["GET"])
def get_monthly_analysis(year, month):
    start_date = datetime(int(year), int(month), 1).date()
    if int(month) == 12:
        end_date = datetime(int(year) + 1, 1, 1).date()
    else:
        end_date = datetime(int(year), int(month) + 1, 1).date()

    entries = ScheduleEntry.query.filter(
        ScheduleEntry.date.between(start_date, end_date)
    ).all()

    return jsonify(calculate_monthly_hours(entries))
