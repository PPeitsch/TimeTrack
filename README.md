# TimeTrack

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![Pytest](https://img.shields.io/badge/Pytest-7.4.0-orange.svg)](https://pytest.org/)
[![Black](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)
[![GitHub license](https://img.shields.io/github/license/PPeitsch/TimeTrack.svg)](LICENSE)
[![Contributions welcome](https://img.shields.io/badge/Contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![codecov](https://codecov.io/gh/PPeitsch/TimeTrack/graph/badge.svg)](https://codecov.io/gh/PPeitsch/TimeTrack)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

TimeTrack is a simple yet powerful time tracking application designed for managing work hours, leaves, and holidays. Built with Flask and compatible with PostgreSQL or SQLite, it provides a user-friendly interface for tracking your time and analyzing your work patterns.


## Features

- 🗓️ **Interactive Calendar Log** - Manage your schedule with a drag-and-drop monthly calendar view
- 📅 **Flexible Time Entry** - Record multiple clock in/out entries per day
- ⚙️ **Customizable Absence Codes** - Create, edit, and delete your own absence types
- 🏖️ **Absence Management** - Track leaves, holidays and other time off
- 📊 **Time Analytics** - View daily, weekly and monthly work summaries
- 📈 **Automatic Calculations** - Track work hour balances and overtime
- 🇦🇷 **Argentina Holidays Integration** - Automatic holiday tracking for Argentina
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🔌 **Flexible Database Support** - Works with SQLite or PostgreSQL
- 🧪 **Well-tested Code** - Comprehensive test suite ensures reliability

## Quick Start

### Prerequisites

- Python 3.9+
- pip (Python package installer)
- PostgreSQL (optional, SQLite works out of the box)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/PPeitsch/TimeTrack.git
cd TimeTrack
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your preferred settings
# Note: Ensure HOLIDAY_PROVIDER is set to ARGENTINA_API for reliable holiday data
```

5. Initialize the database:
```bash
python init_db.py
```
> **Note:** This script is interactive: it asks for the login user and password, and may prompt you to import data such as public holidays.

   On an existing database, apply migrations and set the login with:
```bash
flask db upgrade
flask user set-password <username>
```

6. Run the application:
```bash
flask run
```

7. Access the application at `http://localhost:5000`

### Login and demo mode

TimeTrack is single-user: there is one account, protected by username and password.
Change it at any time with `flask user set-password <username>`.

To publish a demo that anyone can try, create the demo account and enable `DEMO_MODE`;
the login page then shows the credentials:

```bash
flask user set-password demo        # use the same password as DEMO_PASSWORD
export DEMO_MODE=true DEMO_USERNAME=demo DEMO_PASSWORD=demo
```

In production set a strong `SECRET_KEY` (the app refuses to start without one) and,
behind HTTPS, `SESSION_COOKIE_SECURE=true`.

## Usage

The application is organized into several key sections accessible from the main navigation bar.

### Calendar Log

This is the main interface for managing your schedule.
- View an entire month at a glance with color-coded day types.
- Click and drag to select one or more days to change their type (e.g., assign a week of vacation).
- Quickly override weekends or holidays to log work on non-standard days.

### Manual Entry

For detailed time logging on a specific day:
- Select a date and specify whether it's a workday or an absence.
- For workdays, enter multiple clock-in and clock-out times to account for breaks.

### Summary

Get a detailed overview of your logged time for any given month:
- See a summary of required hours, completed hours, and the resulting balance.
- View a day-by-day breakdown of hours worked versus required hours.

### Settings

Customize the application to fit your needs:
- Manage absence codes by adding, editing, or deleting types (e.g., "Vacation", "Sick Leave").

## Project Structure

```
TimeTrack/
├── app/
│   ├── config/        # Configuration settings
│   ├── db/            # Database management
│   ├── models/        # Data models
│   ├── routes/        # Route handlers (Blueprints)
│   ├── services/      # Business logic (e.g., holiday providers)
│   ├── static/        # Static assets (JS, CSS)
│   ├── templates/     # HTML templates
│   └── utils/         # Utility functions
├── scripts/           # Helper scripts
├── tests/             # Test suite
├── .env               # Environment configuration
├── .env.example       # Example environment configuration
├── run.py             # Application entry point
├── init_db.py         # Database initialization script
└── requirements.txt   # Python dependencies
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

We use Black and isort for code formatting:

```bash
# Format code with Black
python -m black .

# Sort imports with isort
python -m isort --profile black .

# Run both with our helper script
python scripts/run-formatters.ps1  # Windows
./scripts/run-formatters.sh  # Linux/Mac
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

Please read our [Contributing Guidelines](CONTRIBUTING.md) and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/) - The web framework used
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM for database operations
- [Bootstrap](https://getbootstrap.com/) - Frontend framework
