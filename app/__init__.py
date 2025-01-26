from flask import Flask
from flask_migrate import Migrate

from app.db.database import db, init_db
from app.routes.manual_entry import manual_entry
from app.routes.time_analysis import time_analysis


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

    init_db(app)
    Migrate(app, db)

    app.register_blueprint(manual_entry)
    app.register_blueprint(time_analysis)

    return app
