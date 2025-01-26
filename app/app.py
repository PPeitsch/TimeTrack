from config.config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.routes.manual_entry import manual_entry
from app.routes.time_analysis import time_analysis

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

app.register_blueprint(manual_entry)
app.register_blueprint(time_analysis)

if __name__ == "__main__":
    app.run(debug=True)
