import getpass
import importlib.util
import os
import re
import secrets
import sys
import time
from pathlib import Path


def parse_env_file(file_path):
    """Parse an env file and return a dictionary of key-value pairs."""
    env_vars = {}
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key, value = parts
                        env_vars[key] = value.strip("'\"")
    return env_vars


def extract_db_info(db_url):
    """Extract database connection info from a DATABASE_URL string."""
    if db_url.startswith("sqlite:///"):
        return {"type": "sqlite", "path": db_url.replace("sqlite:///", "")}

    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", db_url)
    if match:
        return {
            "type": "postgres",
            "user": match.group(1),
            "password": match.group(2),
            "host": match.group(3),
            "port": match.group(4),
            "name": match.group(5),
        }
    return {"type": "unknown"}


def initialize_database_manually():
    """Initialize database tables using direct Python imports."""
    app = None
    try:
        print("\nInitializing the database...")
        sys.path.append(os.getcwd())

        from app import create_app
        from app.config.config import Config
        from app.db.database import db
        from app.utils.init_data import init_data  # Import the data seeder

        app = create_app(Config)

        with app.app_context():
            # Same path as production: the schema comes only from the migrations.
            if not create_schema(db):
                return False, "existing database without migration history"
            print("Schema up to date (flask db upgrade).")

            # Populate initial data (absence codes, default employee)
            init_data()
            print("Default absence codes ready.")

            ensure_login()

            demo = (
                input("\nLoad sample data for the last few months? (y/n) [n]: ")
                .strip()
                .lower()
                == "y"
            )
            if demo:
                from app.services.demo_data import seed_demo_entries

                print(f"{seed_demo_entries()} sample days created.")

            populate = input("\nLoad public holidays now? (y/n) [y]: ").lower() != "n"
            if populate:
                from app.services.holiday_sync import refresh_holidays

                current_year = time.localtime().tm_year
                for year in (current_year, current_year + 1):
                    try:
                        count = refresh_holidays(year)
                        print(f"{year}: {count} holidays saved.")
                    except Exception as error:
                        db.session.rollback()
                        print(f"{year}: could not fetch holidays ({error}).")
                print(
                    "Later years load on their own when viewed, or with "
                    "'flask holidays refresh <year>'."
                )

        print("\nThe database is ready.")
        return True, "Database initialized"

    except Exception as e:
        error_message = f"Database setup failed: {e}"
        print(f"ERROR: {error_message}")
        if app:
            with app.app_context():
                if db.session.is_active:
                    db.session.rollback()
                    print("Database session rolled back.")
        return False, str(e)


def create_schema(db):
    """Apply the migrations; refuse a database created by db.create_all()."""
    from flask_migrate import upgrade  # type: ignore
    from sqlalchemy import inspect

    tables = set(inspect(db.engine).get_table_names())
    if tables and "alembic_version" not in tables:
        print(
            "\nThe database has tables but no migration history (an old version of "
            "init_db.py created it).\nIf the schema matches the latest version, mark "
            "it with 'flask db stamp head' and run this script again."
        )
        return False
    upgrade(directory=str(Path(__file__).resolve().parent / "migrations"))
    return True


def ensure_login():
    """Ask for the TimeTrack login if the default user has no password yet."""
    from app.auth import DEFAULT_EMPLOYEE_ID, set_credentials
    from app.db.database import db
    from app.models.models import Employee

    employee = db.session.get(Employee, DEFAULT_EMPLOYEE_ID)
    if employee is not None and employee.password_hash:
        print(f"Existing login user: {employee.username}")
        return

    print("\nTimeTrack login")
    username = input("Username [admin]: ").strip() or "admin"
    while True:
        password = getpass.getpass("Password: ")
        if password and password == getpass.getpass("Repeat password: "):
            break
        print("The passwords are empty or do not match. Try again.")
    set_credentials(username, password)
    print(f"User '{username}' configured.")


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = {
        "flask": "flask",
        "flask-sqlalchemy": "flask_sqlalchemy",
        "flask-migrate": "flask_migrate",
        "requests": "requests",
        "beautifulsoup4": "bs4",
    }
    missing_packages = []
    for pip_name, import_name in required_packages.items():
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(pip_name)
    return missing_packages


def main():
    print("=== TimeTrack database setup ===")

    missing_packages = check_dependencies()
    if missing_packages:
        print(f"\nMissing dependencies: {', '.join(missing_packages)}")
        print("Install them first: pip install -r requirements.txt")
        sys.exit(1)

    env_path = ".env"
    env_example_path = ".env.example"
    using_existing = False
    if os.path.exists(env_path):
        print(f"\nFound existing {env_path}.")
        env_vars = parse_env_file(env_path)
        using_existing = True
    elif os.path.exists(env_example_path):
        print(f"No {env_path} found, using {env_example_path} as a template.")
        env_vars = parse_env_file(env_example_path)
    else:
        print("No configuration file found. A new one will be created.")
        env_vars = {
            "DATABASE_URL": "sqlite:///timetrack.db",
            "SECRET_KEY": secrets.token_hex(32),
            "FLASK_APP": "run.py",
            "FLASK_ENV": "development",
            "FLASK_DEBUG": "1",
            "HOLIDAY_COUNTRY": "AR",
        }

    if "FLASK_APP" not in env_vars or "run.py" not in env_vars.get("FLASK_APP", ""):
        env_vars["FLASK_APP"] = "run.py"
        print("\nFLASK_APP set to run.py")

    db_url = env_vars.get("DATABASE_URL", "")
    db_info = extract_db_info(db_url)

    if using_existing:
        print("\nCurrent configuration:")
        print(f"  Database: {db_info.get('type', 'unknown')}")
        print(f"  Holiday country: {env_vars.get('HOLIDAY_COUNTRY') or 'AR (default)'}")
        modify = input("\nChange the configuration? (y/n) [n]: ").lower() == "y"
    else:
        modify = True

    if modify:
        print("\nDatabase type:")
        print("  1. SQLite (default)")
        print("  2. PostgreSQL")
        db_choice = ""
        while db_choice not in ["1", "2"]:
            db_choice = input("Choose an option [1]: ").strip() or "1"

        if db_choice == "1":
            sqlite_path = input("SQLite file [timetrack.db]: ") or "timetrack.db"
            env_vars["DATABASE_URL"] = f"sqlite:///{sqlite_path}"
        else:
            db_name = input("Database name [timetrack]: ") or "timetrack"
            db_user = input("PostgreSQL user [postgres]: ") or "postgres"
            db_pass = getpass.getpass("PostgreSQL password: ")
            db_host = input("PostgreSQL host [localhost]: ") or "localhost"
            db_port = input("PostgreSQL port [5432]: ") or "5432"
            env_vars["DATABASE_URL"] = (
                f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            )

        country = input(
            f"Holiday country, ISO code [{env_vars.get('HOLIDAY_COUNTRY') or 'AR'}]: "
        ).strip()
        if country:
            env_vars["HOLIDAY_COUNTRY"] = country.upper()

    modify_secret = input("\nChange the SECRET_KEY? (y/n) [n]: ").lower() == "y"
    if modify_secret:
        use_generated = input("Generate a random key? (y/n) [y]: ").lower() != "n"
        env_vars["SECRET_KEY"] = (
            secrets.token_hex(32) if use_generated else input("SECRET_KEY: ")
        )

    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    print(f"\n{env_path} {'updated' if using_existing else 'created'}.")

    for key, value in env_vars.items():
        os.environ[key] = value

    success, message = initialize_database_manually()

    if success:
        print("\nSetup complete. Start the app with 'flask run'.")
    else:
        print(f"\nERROR: could not initialize the database: {message}")
        print("\nTo debug, run these commands by hand:")
        print("  flask db upgrade")
        print("  flask seed defaults")
        print("  flask user set-password <username>")


if __name__ == "__main__":
    main()
