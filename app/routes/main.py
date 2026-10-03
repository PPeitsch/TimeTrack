"""The four screens of the app: Today, Calendar, Reports and Settings."""

import csv
import io
from calendar import monthrange
from datetime import date, timedelta

from babel.dates import get_day_names
from flask import Blueprint, Response, render_template, request
from flask_babel import get_locale

from app.auth import current_employee_id
from app.services.calendar_service import resolve_days, summarize

main = Blueprint("main", __name__)


def _month_from_args():
    """Year and month from ?year=&month=, defaulting to the current month."""
    today = date.today()
    try:
        if request.args.get("ym"):  # <input type="month"> sends YYYY-MM
            year, month = (int(x) for x in request.args["ym"].split("-"))
        else:
            year = int(request.args.get("year", today.year))
            month = int(request.args.get("month", today.month))
        date(year, month, 1)
    except ValueError:
        year, month = today.year, today.month
    return year, month


def _month_days(year: int, month: int):
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return resolve_days(current_employee_id(), start, end)


@main.route("/")
def index():
    today = date.today()
    employee_id = current_employee_id()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    return render_template(
        "index.html",
        today=resolve_days(employee_id, today, today)[0],
        week=summarize(resolve_days(employee_id, week_start, today)),
        month=summarize(resolve_days(employee_id, month_start, today)),
    )


@main.route("/calendar")
def calendar():
    names = get_day_names("abbreviated", locale=get_locale())
    return render_template("calendar.html", weekday_names=[names[i] for i in range(7)])


@main.route("/reports")
def reports():
    year, month = _month_from_args()
    days = _month_days(year, month)
    first = date(year, month, 1)
    prev_month = first - timedelta(days=1)
    next_month = first + timedelta(days=32)
    return render_template(
        "reports.html",
        days=days,
        totals=summarize(days),
        year=year,
        month=month,
        first=first,
        prev_month=prev_month,
        next_month=next_month,
        today=date.today(),
    )


@main.route("/reports/export.csv")
def export_csv():
    year, month = _month_from_args()
    days = _month_days(year, month)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["date", "type", "entries", "worked", "required", "balance", "observation"]
    )
    for d in days:
        writer.writerow(
            [
                d.date.isoformat(),
                d.type,
                " ".join(f"{e['entry']}-{e['exit']}" for e in d.entries),
                f"{d.worked:.2f}",
                f"{d.required:.2f}",
                f"{d.difference:.2f}",
                d.observation or "",
            ]
        )
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=timetrack-{year}-{month:02d}.csv"
        },
    )


@main.route("/settings")
def settings():
    return render_template("settings.html")
