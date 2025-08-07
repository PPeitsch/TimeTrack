from flask import Blueprint, jsonify, render_template, request

from app.db.database import db
from app.models.models import AbsenceCode

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/absences", methods=["GET"])
def manage_absences_page():
    """Renders the absence code management page."""
    return render_template("settings_absences.html")


# --- API Endpoints ---


@settings_bp.route("/api/absence-codes", methods=["GET"])
def get_absence_codes():
    """Returns a list of all available absence codes."""
    try:
        codes = AbsenceCode.query.order_by(AbsenceCode.code).all()
        return jsonify([{"id": code.id, "code": code.code} for code in codes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/absence-codes", methods=["POST"])
def create_absence_code():
    """Creates a new absence code."""
    data = request.json
    if not data or not data.get("code"):
        return jsonify({"error": "Code is required"}), 400

    new_code_str = data["code"].strip()
    if not new_code_str:
        return jsonify({"error": "Code cannot be empty"}), 400

    existing_code = AbsenceCode.query.filter_by(code=new_code_str).first()
    if existing_code:
        return jsonify({"error": "Code already exists"}), 409  # Conflict

    try:
        new_code = AbsenceCode(code=new_code_str)
        db.session.add(new_code)
        db.session.commit()
        return jsonify({"id": new_code.id, "code": new_code.code}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/absence-codes/<int:code_id>", methods=["PUT"])
def update_absence_code(code_id):
    """Updates an existing absence code."""
    data = request.json
    if not data or not data.get("code"):
        return jsonify({"error": "Code is required"}), 400

    new_code_str = data["code"].strip()
    if not new_code_str:
        return jsonify({"error": "Code cannot be empty"}), 400

    code_to_update = AbsenceCode.query.get(code_id)
    if not code_to_update:
        return jsonify({"error": "Code not found"}), 404

    # Check if the new name conflicts with another existing code
    existing_code = AbsenceCode.query.filter(
        AbsenceCode.id != code_id, AbsenceCode.code == new_code_str
    ).first()
    if existing_code:
        return jsonify({"error": "Another code with this name already exists"}), 409

    try:
        code_to_update.code = new_code_str
        db.session.commit()
        return jsonify({"id": code_to_update.id, "code": code_to_update.code})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/absence-codes/<int:code_id>", methods=["DELETE"])
def delete_absence_code(code_id):
    """Deletes an absence code."""
    code_to_delete = AbsenceCode.query.get(code_id)
    if not code_to_delete:
        return jsonify({"error": "Code not found"}), 404

    try:
        db.session.delete(code_to_delete)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        # Handle cases where the code is in use (foreign key constraint)
        if "violates foreign key constraint" in str(e).lower():
            return (
                jsonify({"error": "Cannot delete code, it is currently in use."}),
                409,
            )
        return jsonify({"error": str(e)}), 500
