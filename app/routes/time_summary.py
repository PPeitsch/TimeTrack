from calendar import monthrange
from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, redirect, url_for
from flask_babel import gettext as _

from app.auth import current_employee_id
from app.services.calendar_service import resolve_day, resolve_days, summarize

time_summary = Blueprint("time_summary", __name__, url_prefix="/summary")


@time_summary.route("/", methods=["GET"])
def show_summary():
    """Old summary URL; merged into /reports."""
    return redirect(url_for("main.reports"), code=301)


@time_summary.route("/daily/<date>", methods=["GET"])
def get_daily_summary(date):
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": _("Invalid date format")}), 400

    try:
        day = resolve_day(current_employee_id(), date_obj)
        return jsonify(
            {
                "type": day.type,
                "hours": day.worked,
                "required": day.required,
                "difference": day.difference,
                "absence_code": day.absence_code,
            }
        )
    except Exception:
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500


@time_summary.route("/monthly/<int:year>/<int:month>", methods=["GET"])
def get_monthly_summary(year, month):
    try:
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        days = resolve_days(current_employee_id(), start_date, end_date)
        return jsonify(summarize(days))
    except Exception:
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500
