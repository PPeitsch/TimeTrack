import secrets

from flask import Flask, flash, redirect, request, url_for
from flask_babel import gettext as _
from flask_migrate import Migrate  # type: ignore

from app.auth import init_auth
from app.db.database import db, init_db
from app.i18n import init_i18n
from app.routes.api import api_bp
from app.routes.main import main
from app.routes.manual_entry import manual_entry
from app.routes.monthly_log import monthly_log_bp
from app.routes.ops import ops_bp
from app.routes.settings import settings_bp
from app.routes.time_log import time_log
from app.routes.time_summary import time_summary
from app.utils.time_calculator import format_hours


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)
    _ensure_secret_key(app)

    init_db(app)
    migrate = Migrate(app, db)
    init_auth(app)
    init_i18n(app)

    app.register_blueprint(main)
    app.register_blueprint(manual_entry)
    app.register_blueprint(time_summary)
    app.register_blueprint(time_log)
    app.register_blueprint(monthly_log_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(ops_bp)

    from app.routes.import_log import import_log_bp

    app.register_blueprint(import_log_bp)

    from app.services.holiday_sync import holidays_cli

    app.cli.add_command(holidays_cli)

    from app.cli import seed_cli

    app.cli.add_command(seed_cli)

    app.add_template_filter(format_hours, "hours")

    @app.errorhandler(413)
    def file_too_large(_error):
        flash(_("File is too large"), "error")
        return redirect(url_for("main.settings", _anchor="import"))

    return app


def _ensure_secret_key(app: Flask) -> None:
    """Fail fast without SECRET_KEY, except in debug/testing where a random one is fine."""
    if app.config.get("SECRET_KEY"):
        return
    if app.debug or app.testing:
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        return
    raise RuntimeError(
        "SECRET_KEY is not set. Define it in the environment or in .env "
        "(e.g. python -c 'import secrets; print(secrets.token_hex(32))')."
    )
