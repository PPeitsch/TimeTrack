from calendar import monthrange
from datetime import date

from flask import Blueprint, current_app, jsonify, redirect, url_for
from flask_babel import gettext as _

from app.auth import current_employee_id
from app.services.calendar_service import resolve_days

time_log = Blueprint("time_log", __name__, url_prefix="/logs")


@time_log.route("/", methods=["GET"])
def show_logs():
    """Old time log URL; merged into /reports."""
    return redirect(url_for("main.reports"), code=301)


@time_log.route("/monthly/<int:year>/<int:month>", methods=["GET"])
def get_monthly_logs(year, month):
    """List the days of the month that have an explicit entry."""
    try:
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        days = resolve_days(current_employee_id(), start_date, end_date)
        return jsonify(
            [
                {
                    "date": d.date.strftime("%Y-%m-%d"),
                    "type": d.type,
                    "entries": d.entries,
                    "total_hours": d.worked,
                    "observation": d.observation,
                }
                for d in days
                if d.has_entry
            ]
        )
    except Exception:
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500
