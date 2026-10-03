import os

from app import create_app
from app.config.config import Config

app = create_app(Config)

if __name__ == "__main__":
    # Never hardcode debug: the Werkzeug debugger allows remote code execution.
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
