# TimeTrack Development Protocol for AI Agents

## Environment

Contributors use Linux, macOS and Windows. Detect the host OS and shell before running
commands, and adapt them:

- **Linux / macOS**: `source .venv/bin/activate`, paths with `/`
- **Windows (PowerShell)**: `.venv\Scripts\Activate.ps1`, paths with `\`

The examples below use POSIX shell syntax.

---

## Project Overview

**TimeTrack** is a self-hosted, single-user Flask app to log working hours and track the
balance against the required hours, with public holidays and absences.
- Data persistence with SQLAlchemy on PostgreSQL or SQLite; the schema comes only from the
  Alembic migrations in `migrations/`.
- Flask Blueprints, server-rendered Jinja templates plus a small JSON API for the calendar.
- English / Spanish interface with Flask-Babel.

## Build System & Tooling

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **pip** | Dependency Manager | `requirements.txt`, `requirements-dev.txt` |
| **black** | Code formatting | default, 88 chars |
| **isort** | Import sorting | `profile = "black"` |
| **mypy** | Type checking | `mypy.ini` |
| **pytest** | Testing | default |
| **Docker** | Container image and local stack | `Dockerfile`, `docker-compose.yml` |

## Python Version Support

- Python 3.10, 3.11+ (CI and the Docker image use 3.11)

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env            # e.g. DATABASE_URL=sqlite:///timetrack.db
flask db upgrade
flask seed demo                 # sample data and the demo login
flask run
```

Or the full stack with PostgreSQL: `docker compose up --build`.

## Code Quality Commands

### Formatting
```bash
# Check formatting
black --check app tests
isort --check-only app tests

# Apply formatting
black app tests
isort app tests
```

### Type Checking
```bash
mypy app
```

### Testing
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Project Structure

```
TimeTrack/
├── app/                     # Main application package
│   ├── __init__.py          # App factory
│   ├── cli.py               # flask seed commands
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # Flask routes/blueprints
│   ├── services/            # Day logic, holidays, importers, demo data
│   ├── templates/           # HTML templates
│   ├── translations/        # Flask-Babel catalogs
│   └── static/              # CSS, JS, icons, vendored Bootstrap
├── docker/                  # Container entrypoint
├── tests/                   # Test suite
├── migrations/              # Database migrations
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── run.py                   # Entry point
└── README.md                # Project overview
```

## Key Guidelines for AI Agents

1. **Always run quality checks** before committing: `black`, `isort`, `mypy`, `pytest`
2. **Use type hints** for all new functions and methods
3. **Write tests** for new functionality
4. **Follow Flask Best Practices**: application factories, blueprints.
5. **Schema changes go through a migration** (`flask db migrate`), never `db.create_all()`.
6. **User-visible texts are translatable** (`_()` / `_l()`), and the Spanish catalog is updated.
7. **No emojis** in code, UI, CLI output, commits or docs; use the SVG icon set for icons.
8. **Record user-visible changes** in the `[Unreleased]` section of `CHANGELOG.md`.
