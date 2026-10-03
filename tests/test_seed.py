from datetime import date

from app.db.database import db
from app.models.models import AbsenceCode, Employee, Holiday, ScheduleEntry
from app.services.demo_data import seed_demo_entries
from app.utils.time_calculator import calculate_daily_hours


def test_seed_demo_entries_fills_past_weekdays(app):
    with app.app_context():
        db.session.add(Employee(id=1, name="Demo"))
        db.session.add(Holiday(date=date(2026, 9, 1), description="Test", type="X"))
        db.session.commit()

        created = seed_demo_entries(months=2, today=date(2026, 9, 15))

        rows = ScheduleEntry.query.order_by(ScheduleEntry.date).all()
        assert created == len(rows) > 0
        dates = [row.date for row in rows]
        assert dates[0] >= date(2026, 8, 1)
        assert dates[-1] <= date(2026, 9, 14)
        assert all(d.weekday() < 5 for d in dates)
        assert date(2026, 9, 1) not in dates
        assert any(row.absence_code == "Vacation" for row in rows)
        for row in rows:
            if row.absence_code is None:
                assert 7 <= calculate_daily_hours(row.entries) <= 10


def test_seed_demo_entries_keeps_existing_days(app):
    with app.app_context():
        db.session.add(Employee(id=1, name="Demo"))
        db.session.add(
            ScheduleEntry(
                employee_id=1,
                date=date(2026, 9, 14),
                entries=[{"entry": "10:00", "exit": "11:00"}],
            )
        )
        db.session.commit()

        first = seed_demo_entries(months=1, today=date(2026, 9, 15))
        again = seed_demo_entries(months=1, today=date(2026, 9, 15))

        assert again == 0
        kept = ScheduleEntry.query.filter_by(date=date(2026, 9, 14)).one()
        assert kept.entries == [{"entry": "10:00", "exit": "11:00"}]
        assert ScheduleEntry.query.count() == first + 1


def test_seed_defaults_command(app):
    result = app.test_cli_runner().invoke(args=["seed", "defaults"])

    assert result.exit_code == 0
    with app.app_context():
        assert db.session.get(Employee, 1) is not None
        assert AbsenceCode.query.filter_by(code="Vacation").first() is not None


def test_seed_demo_command_sets_login_once(app):
    app.config.update(DEMO_USERNAME="demo", DEMO_PASSWORD="secret")
    runner = app.test_cli_runner()

    result = runner.invoke(args=["seed", "demo", "--months", "1"])
    assert result.exit_code == 0, result.output
    assert "Demo login set" in result.output

    with app.app_context():
        employee = db.session.get(Employee, 1)
        assert employee.username == "demo"
        assert employee.check_password("secret")
        employee.set_password("changed")
        db.session.commit()

    result = runner.invoke(args=["seed", "demo", "--months", "1"])
    assert "Demo login set" not in result.output
    with app.app_context():
        assert db.session.get(Employee, 1).check_password("changed")
