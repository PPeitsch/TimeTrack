from flask import Flask, redirect, url_for
from flask_migrate import Migrate

from app.db.database import db, init_db
from app.routes.main import main
from app.routes.manual_entry import manual_entry
from app.routes.time_summary import time_summary


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

    init_db(app)
    migrate = Migrate(app, db)

    app.register_blueprint(main)
    app.register_blueprint(manual_entry)
    app.register_blueprint(time_summary)

    @app.route("/analysis")
    def redirect_old_analysis():
        return redirect(url_for("time_summary.show_summary"))

    return app
