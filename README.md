# TimeTrack

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![Pytest](https://img.shields.io/badge/Pytest-7.4.0-orange.svg)](https://pytest.org/)
[![Black](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)
[![GitHub license](https://img.shields.io/github/license/PPeitsch/TimeTrack.svg)](LICENSE)
[![Contributions welcome](https://img.shields.io/badge/Contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Code coverage](https://img.shields.io/badge/Coverage-90%25-green.svg)](https://codecov.io/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

TimeTrack is a simple yet powerful time tracking application designed for managing work hours, leaves, and holidays. Built with Flask and compatible with PostgreSQL or SQLite, it provides a user-friendly interface for tracking your time and analyzing your work patterns.

![TimeTrack Dashboard](https://via.placeholder.com/800x400?text=TimeTrack+Dashboard)

## 🌟 Features

- 📅 **Flexible Time Entry** - Record multiple clock in/out entries per day
- 🏖️ **Absence Management** - Track leaves, holidays and other time off
- 📊 **Time Analytics** - View daily, weekly and monthly work summaries
- 📈 **Automatic Calculations** - Track work hour balances and overtime
- 🇦🇷 **Argentina Holidays Integration** - Automatic holiday tracking for Argentina
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🔌 **Flexible Database Support** - Works with SQLite or PostgreSQL
- 🧪 **Well-tested Code** - Comprehensive test suite ensures reliability

## 🚀 Quick Start

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
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
flask run
```

7. Access the application at http://localhost:5000

## 📖 Usage

### Manual Time Entry

1. Navigate to "Manual Entry" to record your work hours
2. Select a date and whether it's a regular work day or absence
3. For work days, enter your clock-in and clock-out times
4. You can add multiple time entries per day (e.g., for lunch breaks)

### Time Summary

View a monthly summary of your work hours, including:
- Required hours based on working days
- Actual hours worked
- Balance (overtime or deficit)
- Daily breakdown with detailed information

### Time Logs

Access a chronological log of all your time entries, including:
- Regular work days with specific times
- Absences and holidays
- Daily totals

## 📁 Project Structure

```
TimeTrack/
├── app/
│   ├── config/        # Configuration settings
│   ├── db/            # Database management
│   ├── models/        # Data models
│   ├── routes/        # Route handlers
│   ├── static/        # Static assets (JS, CSS)
│   ├── templates/     # HTML templates
│   └── utils/         # Utility functions
├── scripts/           # Helper scripts
├── tests/             # Test suite
├── .env               # Environment configuration
├── .env.example       # Example environment configuration
├── app.py             # Application entry point
├── init_db.py         # Database initialization script
└── requirements.txt   # Python dependencies
```

## 🧪 Development

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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

Please read our [Contributing Guidelines](CONTRIBUTING.md) and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Acknowledgements

- [Flask](https://flask.palletsprojects.com/) - The web framework used
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM for database operations
- [Bootstrap](https://getbootstrap.com/) - Frontend framework
