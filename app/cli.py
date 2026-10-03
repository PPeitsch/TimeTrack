import click
from flask import current_app
from flask.cli import with_appcontext

from app.auth import DEFAULT_EMPLOYEE_ID, set_credentials
from app.db.database import db
from app.models.models import Employee
from app.services.demo_data import seed_demo_entries
from app.utils.init_data import init_data


@click.group("seed")
def seed_cli():
    """Load initial or sample data."""


@seed_cli.command("defaults")
@with_appcontext
def seed_defaults_command() -> None:
    """Create the default user and absence codes (safe to run again)."""
    init_data()
    click.echo("Default user and absence codes ready.")


@seed_cli.command("demo")
@click.option("--months", default=3, show_default=True, help="Months of history.")
@with_appcontext
def seed_demo_command(months: int) -> None:
    """Load sample time entries and, if missing, the demo login.

    The login comes from DEMO_USERNAME / DEMO_PASSWORD and is only set when the
    user has no password yet. Days that already have entries are left alone.
    """
    init_data()
    employee = db.session.get(Employee, DEFAULT_EMPLOYEE_ID)
    if employee is None or not employee.password_hash:
        username = current_app.config["DEMO_USERNAME"]
        set_credentials(username, current_app.config["DEMO_PASSWORD"])
        click.echo(f"Demo login set: user '{username}'.")
    created = seed_demo_entries(months=months)
    click.echo(f"{created} sample days created.")
