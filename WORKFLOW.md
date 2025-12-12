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

---

## 1. Environment Setup

### First Time Setup

```powershell
# Clone the repository
git clone <repo-url>
cd TimeTrack

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 2. Development Cycle

### Writing Code

1. **Make your changes** in `app/`
2. **Add type hints** to all new functions
3. **Write tests** in `tests/` for new functionality

### Code Quality Checks

Run these before every commit:

```powershell
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
