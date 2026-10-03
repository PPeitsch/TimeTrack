from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from flask_babel import gettext as _

from app.db.database import db
from app.models.models import AbsenceCode, ScheduleEntry

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/absences", methods=["GET"])
def manage_absences_page():
    """Old settings URL; the screen now lives at /settings."""
    return redirect(url_for("main.settings"), code=301)


# --- API Endpoints ---


@settings_bp.route("/api/absence-codes", methods=["GET"])
def get_absence_codes():
    """Returns a list of all available absence codes."""
    try:
        codes = AbsenceCode.query.order_by(AbsenceCode.code).all()
        return jsonify([{"id": code.id, "code": code.code} for code in codes])
    except Exception:
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500


@settings_bp.route("/api/absence-codes", methods=["POST"])
def create_absence_code():
    """Creates a new absence code."""
    data = request.json
    if not data or not data.get("code"):
        return jsonify({"error": _("Code is required")}), 400

    new_code_str = data["code"].strip()
    if not new_code_str:
        return jsonify({"error": _("Code cannot be empty")}), 400

    existing_code = AbsenceCode.query.filter_by(code=new_code_str).first()
    if existing_code:
        return jsonify({"error": _("Code already exists")}), 409

    try:
        new_code = AbsenceCode(code=new_code_str)
        db.session.add(new_code)
        db.session.commit()
        return jsonify({"id": new_code.id, "code": new_code.code}), 201
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500


@settings_bp.route("/api/absence-codes/<int:code_id>", methods=["PUT"])
def update_absence_code(code_id):
    """Updates an existing absence code."""
    data = request.json
    if not data or not data.get("code"):
        return jsonify({"error": _("Code is required")}), 400

    new_code_str = data["code"].strip()
    if not new_code_str:
        return jsonify({"error": _("Code cannot be empty")}), 400

    code_to_update = db.session.get(AbsenceCode, code_id)
    if not code_to_update:
        return jsonify({"error": _("Code not found")}), 404

    existing_code = AbsenceCode.query.filter(
        AbsenceCode.id != code_id, AbsenceCode.code == new_code_str
    ).first()
    if existing_code:
        return jsonify({"error": _("Another code with this name already exists")}), 409

    try:
        # Days store the code as text: rename them in the same transaction so
        # they keep pointing at this code.
        old_code = code_to_update.code
        ScheduleEntry.query.filter_by(absence_code=old_code).update(
            {ScheduleEntry.absence_code: new_code_str}, synchronize_session=False
        )
        code_to_update.code = new_code_str
        db.session.commit()
        return jsonify({"id": code_to_update.id, "code": code_to_update.code})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500


@settings_bp.route("/api/absence-codes/<int:code_id>", methods=["DELETE"])
def delete_absence_code(code_id):
    """Deletes an absence code."""
    code_to_delete = db.session.get(AbsenceCode, code_id)
    if not code_to_delete:
        return jsonify({"error": _("Code not found")}), 404

    # Manually check if the code is in use before attempting to delete.
    is_in_use = ScheduleEntry.query.filter_by(absence_code=code_to_delete.code).first()
    if is_in_use:
        return jsonify({"error": _("Cannot delete code, it is currently in use.")}), 409

    try:
        db.session.delete(code_to_delete)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unhandled error")
        return jsonify({"error": _("Internal server error")}), 500
