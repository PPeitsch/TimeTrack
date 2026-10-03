# TimeTrack

[![Tests](https://github.com/PPeitsch/TimeTrack/actions/workflows/test.yaml/badge.svg)](https://github.com/PPeitsch/TimeTrack/actions/workflows/test.yaml)
[![codecov](https://codecov.io/gh/PPeitsch/TimeTrack/graph/badge.svg)](https://codecov.io/gh/PPeitsch/TimeTrack)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![Code style: black](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/github/license/PPeitsch/TimeTrack.svg)](LICENSE)

TimeTrack is a self-hosted, single-user web app to log your working hours and keep track of
your balance: how much you worked against what you were supposed to, day by day, week by week
and month by month. Weekends and public holidays are taken into account automatically, and
absences (vacation, sick leave, your own codes) are one click away.

![Calendar](docs/screenshots/calendar.png)

## Features

- **Today, Calendar, Reports and Settings**: four screens, nothing else to learn.
- **Calendar editing**: click a day to log one or more time ranges, an absence or an
  observation; drag across days (or Shift+click) to change several at once.
- **Balances**: worked, required and balance for the day, the week and the month. Hours on
  weekends and holidays count as overtime.
- **Public holidays for 100+ countries**, loaded automatically the first time a year is viewed
  ([Nager.Date](https://date.nager.at); for Argentina, [ArgentinaDatos](https://argentinadatos.com)).
- **Reports** per month with CSV export.
- **Import** hours from PDF or Excel reports, with a preview before saving.
- **English and Spanish** interface, **light and dark** themes.
- **Login** with CSRF protection and rate limiting; optional demo mode.
- PostgreSQL or SQLite. No external requests from the browser (assets are served locally).

| Today | Day editor | Reports |
|---|---|---|
| ![Today](docs/screenshots/today.png) | ![Day editor](docs/screenshots/day-panel.png) | ![Reports](docs/screenshots/reports.png) |

<details>
<summary>Dark theme</summary>

![Calendar, dark theme](docs/screenshots/calendar-dark.png)

</details>

## Quick start (Docker)

```bash
git clone https://github.com/PPeitsch/TimeTrack.git
cd TimeTrack
docker compose up --build
```

Open <http://localhost:8000> and log in with `demo` / `demo`. This starts the app with
PostgreSQL and three months of sample data; the database lives in a Docker volume.

### Using it for real

Create a `.env` file next to `docker-compose.yml`:

```bash
DEMO_MODE=false
SEED_DEMO=false
HOLIDAY_COUNTRY=ES          # your country, ISO 3166-1 alpha-2
POSTGRES_PASSWORD=change-me
```

Then start it and set your login:

```bash
docker compose up --build -d
docker compose exec web flask user set-password <username>
```

If you already started the demo, run `docker compose down --volumes` first to start from an
empty database. Behind HTTPS, also set `SESSION_COOKIE_SECURE=true`.

## Manual installation

Requires Python 3.10 or newer. PostgreSQL is optional: SQLite works out of the box.

```bash
git clone https://github.com/PPeitsch/TimeTrack.git
cd TimeTrack
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```

Edit `.env` (at least `DATABASE_URL`, `SECRET_KEY` and `HOLIDAY_COUNTRY`), then:

```bash
flask db upgrade                 # create or update the database schema
flask seed defaults              # default user and absence codes
flask user set-password <username>
flask run
```

The app is at <http://localhost:5000>. `python init_db.py` does the same setup interactively
(database, secret key, login and optional sample data).

For production, run it with gunicorn (included in `requirements.txt`):

```bash
gunicorn --bind 0.0.0.0:8000 --workers 2 run:app
```

## Configuration

Settings are read from the environment or from `.env`. The most relevant ones:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/timetrack` | Any SQLAlchemy URL, e.g. `sqlite:///timetrack.db`. |
| `SECRET_KEY` | (none) | Required outside debug mode. Generate one with `python -c 'import secrets; print(secrets.token_hex(32))'`. |
| `SECRET_KEY_FILE` | (none) | File that holds the secret key, as an alternative to `SECRET_KEY`. |
| `HOLIDAY_COUNTRY` | `AR` | Country whose public holidays are loaded (ISO 3166-1 alpha-2). |
| `HOLIDAY_PROVIDER` | automatic | `NAGER_DATE`, `ARGENTINA_API` or `ARGENTINA_WEBSITE`. When empty: `ARGENTINA_API` for `AR`, `NAGER_DATE` otherwise. |
| `HOLIDAY_AUTO_FETCH` | `true` | Load a year's holidays the first time it is viewed. |
| `WORKING_HOURS_PER_DAY` | `8` | Required hours on a regular working day. |
| `SESSION_COOKIE_SECURE` | `false` | Send session cookies only over HTTPS. |
| `DEMO_MODE` | `false` | Show the demo credentials on the login page. |
| `DEMO_USERNAME` / `DEMO_PASSWORD` | `demo` / `demo` | Demo credentials (also used by `flask seed demo`). |
| `MAX_UPLOAD_MB` | `10` | Maximum size of imported files. |

The Docker image also reads `SEED_DEMO` (load sample data on start) and `GUNICORN_WORKERS`.
See [`.env.example`](.env.example) for the full list.

## Commands

| Command | What it does |
|---|---|
| `flask db upgrade` | Create or update the database schema. |
| `flask seed defaults` | Create the default user and absence codes (safe to run again). |
| `flask seed demo [--months N]` | Load sample days for the last N months and, if there is no password yet, the demo login. |
| `flask user set-password <username>` | Set the username and password of the single user. |
| `flask holidays refresh [YEAR ...]` | Reload the public holidays of the given years (default: this year and the next). |

## Usage

- **Today**: hours logged today and your balance for the week and the month so far.
- **Calendar**: the month at a glance, Monday first, with holidays, weekends, absences and hours
  per day. Click a day to mark it as work (one or more time ranges), as an absence, or back to
  the default of the base calendar, and to add an observation. Drag across days, or Shift+click,
  to change several days at once.
- **Reports**: a month table with times, worked, required and balance per day, with totals and
  CSV export.
- **Settings**: absence codes (renaming a code also renames it on the days that use it) and
  import from PDF or Excel, with a preview where you choose whether to replace or skip days that
  already have data.

TimeTrack is single-user: there is one account. To publish a demo anyone can try, set
`DEMO_MODE=true` and run `flask seed demo`; the login page then shows the credentials.

## Languages

The interface is available in English and Spanish. The EN / ES switch in the navbar (also on the
login page) changes the language; without a choice, the browser's language is used.

To change or add texts:

```bash
pybabel extract -F babel.cfg -k _l --no-location --sort-output -o app/translations/messages.pot .
pybabel update -i app/translations/messages.pot -d app/translations
# edit app/translations/es/LC_MESSAGES/messages.po
pybabel compile -d app/translations
```

Texts used by the JavaScript are listed in `js_messages()` in `app/i18n.py`. To add a language,
run `pybabel init -i app/translations/messages.pot -d app/translations -l <code>` and add it to
`LANGUAGES`.

## Project structure

```
TimeTrack/
├── app/
│   ├── config/        # Settings read from the environment
│   ├── db/            # SQLAlchemy setup
│   ├── models/        # Data models
│   ├── routes/        # Blueprints (screens and JSON API)
│   ├── services/      # Day logic, holidays, importers, demo data
│   ├── static/        # CSS, JavaScript, icons, vendored Bootstrap
│   ├── templates/     # Jinja templates
│   ├── translations/  # Spanish catalog
│   └── utils/
├── docker/            # Container entrypoint
├── docs/screenshots/
├── migrations/        # Alembic migrations (the only source of the schema)
├── tests/
├── docker-compose.yml
├── Dockerfile
├── init_db.py         # Interactive first-time setup
└── run.py             # Application entry point
```

## Development

```bash
pip install -r requirements-dev.txt
pre-commit install

black app tests && isort app tests   # format
mypy app                             # type check
pytest tests/                        # tests
```

See [WORKFLOW.md](WORKFLOW.md) for the full development cycle and
[CONTRIBUTING.md](.github/CONTRIBUTING.md) before opening an issue or a pull request.

## Contributing

Contributions are welcome. Please read the [contributing guidelines](.github/CONTRIBUTING.md)
and the [code of conduct](.github/CODE_OF_CONDUCT.md). To report a security issue, see
[SECURITY.md](.github/SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/), [SQLAlchemy](https://www.sqlalchemy.org/) and
  [Bootstrap](https://getbootstrap.com/).
- [Nager.Date](https://date.nager.at) and [ArgentinaDatos](https://argentinadatos.com) for
  public holiday data.
