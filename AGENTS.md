# TimeTrack Development Protocol for AI Agents

## OS Context

This project is developed primarily on **Windows**. Detect the host OS and adapt commands accordingly:

- **Windows**: Use `.venv\Scripts\Activate.ps1`, paths with `\`
- **Linux**: Use `source .venv/bin/activate`, paths with `/`

When in doubt, ask the user which environment they are working on.

---

## Project Overview

**TimeTrack** is a Flask-based web application for tracking time entry and observations.
- Data persistence with SQLAlchemy and PostgreSQL/SQLite.
- MVC architecture with Flask Blueprints.

## Build System & Tooling

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **pip** | Dependency Manager | `requirements.txt`, `requirements-dev.txt` |
| **black** | Code formatting | `pyproject.toml` (or default), 88 chars |
| **isort** | Import sorting | `profile = "black"` |
| **mypy** | Type checking | `mypy.ini` |
| **pytest** | Testing | `pytest.ini` or default |

## Python Version Support

- Python 3.10, 3.11+

## Development Setup

```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Code Quality Commands

### Formatting
```powershell
# Check formatting
black --check app tests
isort --check-only app tests

# Apply formatting
black app tests
isort app tests
```

### Type Checking
```powershell
mypy app tests
```

### Testing
```powershell
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Project Structure

```
TimeTrack/
├── app/                     # Main application package
│   ├── __init__.py          # App factory
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # Flask routes/blueprints
│   ├── services/            # Business logic
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, Images
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
