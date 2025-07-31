from calendar import monthrange
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from app.models.models import Holiday, ScheduleEntry
from app.utils.time_calculator import calculate_daily_hours

time_summary = Blueprint("time_summary", __name__, url_prefix="/summary")


@time_summary.route("/", methods=["GET"])
def show_summary():
    return render_template("time_summary.html")


@time_summary.route("/daily/<date>", methods=["GET"])
def get_daily_summary(date):
    try:
        # Parse the date string to a datetime object
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        # Fetch relevant records for the day
        entry = ScheduleEntry.query.filter_by(date=date_obj, employee_id=1).first()
        holiday = Holiday.query.filter_by(date=date_obj).first()

        # Determine the type of the day with clear precedence
        day_type = "Work Day"  # Default
        if entry and entry.absence_code:
            day_type = entry.absence_code
        elif holiday:
            day_type = "Holiday"
        elif date_obj.weekday() >= 5:  # 5: Saturday, 6: Sunday
            day_type = "Weekend"

        # Determine required hours and actual hours based on day type
        required_hours = 0.0
        hours_worked = 0.0

        if day_type == "Work Day":
            required_hours = 8.0
            if entry:
                hours_worked = calculate_daily_hours(entry.entries)

        # Final response data
        response_data = {
            "type": day_type,
            "hours": hours_worked,
            "required": required_hours,
            "difference": hours_worked - required_hours,
            "absence_code": entry.absence_code if entry else None,
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@time_summary.route("/monthly/<int:year>/<int:month>", methods=["GET"])
def get_monthly_summary(year, month):
    try:
        start_date = date(year, month, 1)
        _, days_in_month = monthrange(year, month)
        end_date = date(year, month, days_in_month)

        # Fetch all relevant data for the month in optimized queries
        entries_query = ScheduleEntry.query.filter(
            ScheduleEntry.date.between(start_date, end_date),
            ScheduleEntry.employee_id == 1,
        ).all()
        entries_map = {entry.date: entry for entry in entries_query}

        holidays_query = Holiday.query.filter(
            Holiday.date.between(start_date, end_date)
        ).all()
        holidays_set = {h.date for h in holidays_query}

        total_worked = 0.0
        total_required = 0.0

        current_date = start_date
        while current_date <= end_date:
            entry = entries_map.get(current_date)

            is_work_day = True
            if entry and entry.absence_code:
                is_work_day = False
            elif current_date in holidays_set:
                is_work_day = False
            elif current_date.weekday() >= 5:
                is_work_day = False

            if is_work_day:
                total_required += 8.0
                if entry:
                    total_worked += calculate_daily_hours(entry.entries)

            current_date += timedelta(days=1)

        monthly_data = {
            "total": total_worked,
            "required": total_required,
            "difference": total_worked - total_required,
        }

        return jsonify(monthly_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
