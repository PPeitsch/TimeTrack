import logging
import os
import time
import uuid
from datetime import datetime
from typing import List, Tuple

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_babel import gettext as _
from werkzeug.utils import secure_filename

from app.auth import current_employee_id
from app.db.database import db
from app.models.models import ScheduleEntry
from app.services.importer.factory import ImporterFactory
from app.services.importer.protocol import ImportResult, TimeEntryRecord
from app.utils.validators import validate_entries

logger = logging.getLogger(__name__)


import_log_bp = Blueprint("import_log", __name__, url_prefix="/import")

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = ("pdf", "xlsx")
# overwrite: imported times replace the day's times; skip: days that already
# have an entry are left alone.
IMPORT_MODES = ("overwrite", "skip")


@import_log_bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash(_("No file part"), "error")
            return redirect(url_for("main.settings", _anchor="import"))

        file = request.files["file"]
        if file.filename == "":
            flash(_("No selected file"), "error")
            return redirect(url_for("main.settings", _anchor="import"))

        if file:
            filename = secure_filename(file.filename or "")
            file_ext = filename.split(".")[-1].lower()

            if file_ext not in ALLOWED_EXTENSIONS:
                flash(_("Unsupported file type"), "error")
                return redirect(url_for("main.settings", _anchor="import"))

            _cleanup_stale_uploads()

            # Generate unique ID for this upload
            upload_id = str(uuid.uuid4())
            temp_filename = f"{upload_id}.{file_ext}"
            filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
            file.save(filepath)

            return redirect(url_for("import_log.preview", upload_id=upload_id))

    return redirect(url_for("main.settings", _anchor="import"))


@import_log_bp.route("/preview/<upload_id>", methods=["GET"])
def preview(upload_id):
    # Find file
    filepath = _get_filepath(upload_id)
    if not filepath:
        flash(_("File not found or expired"), "error")
        return redirect(url_for("main.settings", _anchor="import"))

    try:
        result = _parse(filepath)

        return render_template(
            "import_preview.html", result=result, upload_id=upload_id
        )
    except Exception:
        logger.exception("Error parsing upload %s", upload_id)
        flash(_("Error parsing file. Check that it has the expected format."), "error")
        return redirect(url_for("main.settings", _anchor="import"))


@import_log_bp.route("/confirm/<upload_id>", methods=["POST"])
def confirm(upload_id):
    filepath = _get_filepath(upload_id)
    if not filepath:
        flash(_("File not found or expired"), "error")
        return redirect(url_for("main.settings", _anchor="import"))

    try:
        result = _parse(filepath)

        mode = request.form.get("mode", "overwrite")
        if mode not in IMPORT_MODES:
            mode = "overwrite"
        imported, skipped = _apply_records(result.records, current_employee_id(), mode)
        db.session.commit()

        # Cleanup
        os.remove(filepath)

        message = _("Imported %(count)s records.", count=imported)
        if skipped:
            message += " " + _(
                "Skipped %(count)s (existing days or nothing to import).",
                count=skipped,
            )
        flash(message, "success")
        return redirect(url_for("main.calendar"))

    except Exception:
        db.session.rollback()
        logger.exception("Error importing upload %s", upload_id)
        flash(_("Error importing data."), "error")
        return redirect(url_for("import_log.preview", upload_id=upload_id))


@import_log_bp.route("/cancel/<upload_id>", methods=["POST"])
def cancel(upload_id):
    filepath = _get_filepath(upload_id)
    if filepath:
        try:
            os.remove(filepath)
        except OSError:
            logger.warning("Could not remove upload %s", filepath)
    return redirect(url_for("main.settings", _anchor="import"))


def _get_filepath(upload_id):
    """Return the stored file for an upload id, or None.

    The id comes from the URL, so it must be a canonical UUID and match a file
    name exactly (`<uuid>.<ext>`); a prefix match would let `/preview/a` pick
    up (or `cancel` delete) any upload starting with `a`.
    """
    try:
        if str(uuid.UUID(upload_id)) != upload_id:
            return None
    except (ValueError, TypeError):
        return None
    for ext in ALLOWED_EXTENSIONS:
        candidate = os.path.join(UPLOAD_FOLDER, f"{upload_id}.{ext}")
        if os.path.isfile(candidate):
            return candidate
    return None


def _cleanup_stale_uploads():
    """Delete uploads that were previewed but never confirmed or cancelled."""
    max_age = current_app.config.get("UPLOAD_MAX_AGE_HOURS", 24) * 3600
    now = time.time()
    for name in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, name)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > max_age:
                os.remove(path)
        except OSError:
            logger.warning("Could not remove stale upload %s", path)


def _parse(filepath: str) -> ImportResult:
    """Parse an upload and flag records whose times cannot be imported."""
    importer = ImporterFactory.get_importer(filepath)
    with open(filepath, "rb") as f:
        result = importer.parse(f.read())

    for record in result.records:
        if not record.is_valid:
            continue
        if bool(record.entry_time) != bool(record.exit_time):
            record.is_valid = False
            record.error_message = _("Entry and exit times must both be present")
        elif record.entry_time and record.exit_time:
            is_valid, error = validate_entries(
                [{"entry": record.entry_time, "exit": record.exit_time}]
            )
            if not is_valid:
                record.is_valid = False
                record.error_message = error
    result.valid_records = sum(1 for r in result.records if r.is_valid)
    return result


def _apply_records(
    records: List[TimeEntryRecord], employee_id: int, mode: str
) -> Tuple[int, int]:
    """Write valid records for the employee. Returns (imported, skipped).

    A record without times never clears the hours already logged for that day;
    it only sets the observation.
    """
    imported = skipped = 0
    for record in records:
        if not record.is_valid:
            continue

        entry_date = datetime.strptime(record.date, "%Y-%m-%d").date()
        existing = ScheduleEntry.query.filter_by(
            employee_id=employee_id, date=entry_date
        ).first()
        has_times = bool(record.entry_time and record.exit_time)

        if existing is not None and mode == "skip":
            skipped += 1
            continue

        if not has_times:
            if not record.observation:
                skipped += 1
                continue
            if existing is not None:
                existing.observation = record.observation
            else:
                db.session.add(
                    ScheduleEntry(
                        employee_id=employee_id,
                        date=entry_date,
                        entries=[],
                        observation=record.observation,
                    )
                )
            imported += 1
            continue

        entries_data = [{"entry": record.entry_time, "exit": record.exit_time}]
        if existing is not None:
            existing.entries = entries_data
            existing.absence_code = None
            if record.observation:
                existing.observation = record.observation
        else:
            db.session.add(
                ScheduleEntry(
                    employee_id=employee_id,
                    date=entry_date,
                    entries=entries_data,
                    observation=record.observation,
                )
            )
        imported += 1
    return imported, skipped
