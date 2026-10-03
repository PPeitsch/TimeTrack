"""Interface language (English / Spanish).

The language comes from the visitor's choice (stored in the session by the
EN / ES switch), else from the browser's Accept-Language, else English.

Day types ("Work Day", "Weekend", "Holiday") stay in English as stored values
and API identifiers; only their labels are translated. Absence codes are user
data and are shown as written.
"""

from typing import Dict

from flask import Blueprint, has_request_context, redirect, request, session, url_for
from flask_babel import Babel, get_locale
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

LANGUAGES = {"en": "English", "es": "Español"}
DEFAULT_LANGUAGE = "en"

babel = Babel()
i18n_bp = Blueprint("i18n", __name__)

DAY_TYPE_LABELS = {
    "Work Day": _l("Work Day"),
    "Weekend": _l("Weekend"),
    "Holiday": _l("Holiday"),
}


def select_locale() -> str:
    if not has_request_context():  # CLI commands, background work
        return DEFAULT_LANGUAGE
    lang = session.get("lang")
    if lang in LANGUAGES:
        return str(lang)
    return request.accept_languages.best_match(LANGUAGES.keys()) or DEFAULT_LANGUAGE


def day_label(day_type: str) -> str:
    """Display label for a day type; absence codes are returned unchanged."""
    label = DAY_TYPE_LABELS.get(day_type)
    return str(label) if label is not None else day_type


def js_messages() -> Dict[str, str]:
    """Strings used by the JavaScript, translated for the current request."""
    return {
        "Work Day": _("Work Day"),
        "Weekend": _("Weekend"),
        "Holiday": _("Holiday"),
        "close": _("Close"),
        "worked": _("%(hours)s worked", hours="{hours}"),
        "has_observation": _("Has observation"),
        "default_option": _("Default (base calendar)"),
        "default_hint": _(
            '"Default" follows the base calendar: %(type)s.', type="{type}"
        ),
        "load_calendar_error": _("Could not load the calendar."),
        "day_saved": _("Day saved."),
        "save_day_error": _("Could not save the day."),
        "days_selected": _("%(count)s days selected", count="{count}"),
        "days_updated": _("%(count)s days updated.", count="{count}"),
        "save_changes_error": _("Could not save the changes."),
        "load_codes_error": _("Could not load the absence codes."),
        "no_codes": _("No absence codes yet."),
        "edit": _("Rename"),
        "delete": _("Delete"),
        "add_code_error": _("Could not add the code."),
        "update_code_error": _("Could not rename the code."),
        "delete_code_error": _("Could not delete the code."),
        "confirm_delete": _("Delete this absence code? This cannot be undone."),
        "code_added": _("Code added."),
        "code_updated": _("Code renamed."),
        "code_deleted": _("Code deleted."),
    }


@i18n_bp.route("/lang/<code>", methods=["POST"])
def set_language(code):
    if code in LANGUAGES:
        session["lang"] = code
    target = request.form.get("next") or ""
    if not target.startswith("/") or target.startswith("//"):
        target = url_for("main.index")
    return redirect(target)


def init_i18n(app) -> None:
    babel.init_app(app, locale_selector=select_locale)
    app.register_blueprint(i18n_bp)

    @app.context_processor
    def inject_i18n():
        return {
            "LANGUAGES": LANGUAGES,
            "current_language": str(get_locale() or DEFAULT_LANGUAGE),
            "day_label": day_label,
            "js_messages": js_messages,
        }
