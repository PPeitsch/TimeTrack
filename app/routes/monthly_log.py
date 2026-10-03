from calendar import monthrange
from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from flask_babel import gettext as _

from app.auth import current_employee_id
from app.db.database import db
from app.models.models import AbsenceCode, ScheduleEntry
from app.services.calendar_service import resolve_days

monthly_log_bp = Blueprint("monthly_log", __name__, url_prefix="/monthly-log")


@monthly_log_bp.route("/", methods=["GET"])
def view_monthly_log():
    """Old calendar URL; the screen now lives at /calendar."""
    return redirect(url_for("main.calendar"), code=301)


@monthly_log_bp.route("/api/<int:year>/<int:month>", methods=["GET"])
def get_monthly_log_data(year, month):
    """
    Provides the data for all days in a given month for the calendar view.
    """
    try:
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        days = resolve_days(current_employee_id(), start_date, end_date)
        days_data = [{"date": d.date.isoformat(), "type": d.type} for d in days]
        return jsonify(days_data)

    except Exception:
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500


@monthly_log_bp.route("/api/update-days", methods=["POST"])
def update_day_types():
    """
    Updates the type for a list of dates.
    Handles a special "DEFAULT" type to revert to the base calendar state.
    """
    data = request.json
    if not data or "dates" not in data or "day_type" not in data:
        return jsonify({"error": _("Invalid request body")}), 400

    try:
        dates_to_update = [
            datetime.strptime(d, "%Y-%m-%d").date() for d in data["dates"]
        ]
    except (TypeError, ValueError):
        return jsonify({"error": _("Invalid date format")}), 400

    new_day_type = data["day_type"]
    if new_day_type not in ("DEFAULT", "Work Day") and not (
        AbsenceCode.query.filter_by(code=new_day_type).first()
    ):
        return jsonify({"error": _("Unknown day type")}), 400

    try:
        if new_day_type == "DEFAULT":
            # Revert to the base calendar. Days with logged hours or an
            # observation only lose the override, never the data.
            overrides = ScheduleEntry.query.filter(
                ScheduleEntry.employee_id == current_employee_id(),
                ScheduleEntry.date.in_(dates_to_update),
            ).all()
            for entry in overrides:
                if entry.entries or entry.observation:
                    entry.absence_code = None
                else:
                    db.session.delete(entry)
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
        return jsonify({"error": _("Internal server error")}), 500
