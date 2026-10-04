"""Tests for the EN / ES interface language."""

import json
import re
from datetime import date

from app.db.database import db
from app.i18n import day_label
from app.models.models import ScheduleEntry


def i18n_messages(html):
    match = re.search(r"window\.I18N = (\{.*?\});</script>", html)
    return json.loads(match.group(1))


def test_english_by_default(client, default_employee_id):
    html = client.get("/").get_data(as_text=True)
    assert '<html lang="en">' in html
    assert "This week, to date" in html


def test_accept_language_picks_spanish(client, default_employee_id):
    html = client.get("/", headers={"Accept-Language": "es-AR,es;q=0.9"}).get_data(
        as_text=True
    )
    assert '<html lang="es">' in html
    assert "Esta semana, a la fecha" in html


def test_switch_is_remembered_and_returns_to_page(client, default_employee_id):
    response = client.post("/lang/es", data={"next": "/reports"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/reports")
    html = client.get("/calendar").get_data(as_text=True)
    assert "Calendario" in html
    assert "<div>lun</div>" in html  # weekday header from Babel

    client.post("/lang/en", data={"next": "/"})
    assert "Calendar" in client.get("/calendar").get_data(as_text=True)


def test_switch_rejects_external_next_and_unknown_language(client, default_employee_id):
    response = client.post("/lang/fr", data={"next": "//evil.example"})
    assert "evil.example" not in response.headers["Location"]
    assert '<html lang="en">' in client.get("/").get_data(as_text=True)


def test_js_messages_are_translated(client, default_employee_id):
    client.post("/lang/es")
    messages = i18n_messages(client.get("/calendar").get_data(as_text=True))
    assert messages["Work Day"] == "Día laboral"
    assert messages["days_selected"] == "{count} días seleccionados"


def test_api_errors_follow_language(client, default_employee_id):
    client.post("/lang/es")
    response = client.put(
        "/api/days/2025-03-17",
        json={"kind": "work", "entries": [{"entry": "09:00", "exit": "09:00"}]},
    )
    assert (
        response.get_json()["error"] == "La salida tiene que ser distinta de la entrada"
    )


def test_reports_translate_day_types_and_dates(client, default_employee_id):
    db.session.add(ScheduleEntry(employee_id=1, date=date(2025, 3, 17), entries=[]))
    db.session.commit()
    client.post("/lang/es")
    html = client.get("/reports?ym=2025-03").get_data(as_text=True)
    assert "Fin de semana" in html
    assert "lun 17" in html


def test_day_label_keeps_absence_codes(app):
    assert day_label("Vacation") == "Vacation"
    assert day_label("Holiday") == "Holiday"


def test_login_page_has_language_switch(app):
    app.config["LOGIN_DISABLED"] = False
    html = app.test_client().get("/login").get_data(as_text=True)
    assert "/lang/es" in html
