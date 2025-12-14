import dataclasses
import json
import logging
import os
import pathlib
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import List

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from app.db.database import db
from app.models.models import Employee, ScheduleEntry
from app.services.importer.factory import ImporterFactory
from app.services.importer.protocol import ImportResult
from app.utils.time_calculator import calculate_daily_hours

logger = logging.getLogger(__name__)


import_log_bp = Blueprint("import_log", __name__, url_prefix="/import")

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@import_log_bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file", "error")
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename or "")
            file_ext = filename.split(".")[-1].lower()

            if file_ext not in ["pdf", "xlsx", "xls"]:
                flash("Unsupported file type", "error")
                return redirect(request.url)

            # Generate unique ID for this upload
            upload_id = str(uuid.uuid4())
            temp_filename = f"{upload_id}.{file_ext}"
            filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
            file.save(filepath)

            return redirect(url_for("import_log.preview", upload_id=upload_id))

    return render_template("import_upload.html")


@import_log_bp.route("/preview/<upload_id>", methods=["GET"])
def preview(upload_id):
    # Find file
    filepath = _get_filepath(upload_id)
    if not filepath:
        flash("File not found or expired", "error")
        return redirect(url_for("import_log.upload_file"))

    try:
        importer = ImporterFactory.get_importer(filepath)
        with open(filepath, "rb") as f:
            content = f.read()
            result = importer.parse(content)

        return render_template(
            "import_preview.html", result=result, upload_id=upload_id
        )
    except Exception as e:
        flash(f"Error parsing file: {str(e)}", "error")
        return redirect(url_for("import_log.upload_file"))


@import_log_bp.route("/confirm/<upload_id>", methods=["POST"])
def confirm(upload_id):
    filepath = _get_filepath(upload_id)
    if not filepath:
        flash("File not found or expired", "error")
        return redirect(url_for("import_log.upload_file"))

    try:
        importer = ImporterFactory.get_importer(filepath)
        with open(filepath, "rb") as f:
            content = f.read()
            result = importer.parse(content)

        # Import valid records
        count = 0
        # Assume for now we are importing for Employee ID 1 or passed in form
        # Ideally user selects employee in Upload or Preview
        # For now, let's hardcode 1 or get from request if we added it
        employee_id = 1

        for record in result.records:
            if not record.is_valid:
                continue

            # Check duplicate/overwrite?
            entry_date = datetime.strptime(record.date, "%Y-%m-%d").date()
            existing = ScheduleEntry.query.filter_by(
                employee_id=employee_id, date=entry_date
            ).first()

            entries_data = []
            if record.entry_time and record.exit_time:
                entries_data.append(
                    {"entry": record.entry_time, "exit": record.exit_time}
                )

            if existing:
                existing.entries = entries_data
                existing.observation = record.observation
                # If valid entries exist, we assume normal work day, so unset absence?
                if entries_data:
                    existing.absence_code = None
            else:
                new_entry = ScheduleEntry(
                    employee_id=employee_id,
                    date=entry_date,
                    entries=entries_data,
                    observation=record.observation,
                )
                db.session.add(new_entry)
            count += 1

        db.session.commit()

        # Cleanup
        os.remove(filepath)

        flash(f"Successfully imported {count} records", "success")
        return redirect(url_for("monthly_log.view_monthly_log"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error importing data: {str(e)}", "error")
        return redirect(url_for("import_log.preview", upload_id=upload_id))


@import_log_bp.route("/cancel/<upload_id>", methods=["POST"])
def cancel(upload_id):
    filepath = _get_filepath(upload_id)
    if filepath:
        try:
            os.remove(filepath)
        except:
            pass
    return redirect(url_for("import_log.upload_file"))


def _get_filepath(upload_id):
    # Search for file with upload_id prefix
    for f in os.listdir(UPLOAD_FOLDER):
        if f.startswith(upload_id):
            return os.path.join(UPLOAD_FOLDER, f)
    return None
