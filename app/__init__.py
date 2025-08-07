from flask import Flask, redirect, url_for
from flask_migrate import Migrate

from app.db.database import db, init_db
from app.routes.main import main
from app.routes.manual_entry import manual_entry
from app.routes.monthly_log import monthly_log_bp
from app.routes.time_log import time_log
from app.routes.time_summary import time_summary


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

    init_db(app)
    migrate = Migrate(app, db)

    app.register_blueprint(main)
    app.register_blueprint(manual_entry)
    app.register_blueprint(time_summary)
    app.register_blueprint(time_log)
    app.register_blueprint(monthly_log_bp)

    return app
