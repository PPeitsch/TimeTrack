# TimeTrack Development Workflow

This document describes the standard development workflow for contributing to TimeTrack.

---

## Quick Reference

| Task | Command |
|------|---------|
| Format code | `black app tests && isort app tests` |
| Check formatting | `black --check app tests && isort --check-only app tests` |
| Type check | `mypy app` |
| Run tests | `pytest tests/ -v` |
| Run app | `flask run` or `python run.py` |
| Run with Docker | `docker compose up --build` |
| New migration | `flask db migrate -m "..."` |

---

## 1. Environment Setup

### First Time Setup

```bash
# Clone the repository
git clone https://github.com/PPeitsch/TimeTrack.git
cd TimeTrack

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Configure and create the database
cp .env.example .env               # e.g. DATABASE_URL=sqlite:///timetrack.db
flask db upgrade
flask seed demo                    # sample data and the demo login
```

To run the full stack with PostgreSQL instead: `docker compose up --build`.

---

## 2. Development Cycle

### Writing Code

1. **Make your changes** in `app/`
2. **Add type hints** to all new functions
3. **Write tests** in `tests/` for new functionality

### Code Quality Checks

Run these before every commit:

```bash
# Format code
black app tests
isort app tests

# Type checking
mypy app

# Run tests
pytest tests/ -v
```

### Pre-Commit Checklist

- [ ] Code formatted with black
- [ ] Imports sorted with isort
- [ ] mypy passes without errors
- [ ] All tests pass
- [ ] New tests added for new functionality

---
