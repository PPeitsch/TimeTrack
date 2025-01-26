# TimeSheet

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Simple time tracking application for managing work hours, leaves and holidays. Built with Flask and PostgreSQL.

## 🌟 Features

- 📅 Manual time entry with multiple clock in/out per day
- 📊 Daily, weekly and monthly time analysis
- 🏖️ Leave management and holiday tracking
- 📈 Automatic hour calculations
- 🇦🇷 Argentina holidays integration

## 🚀 Quick Start

1. Clone and setup:
```bash
git clone https://github.com/yourusername/timesheet.git
cd timesheet
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Initialize database:
```bash
flask db init
flask db migrate
flask db upgrade
```

4. Run application:
```bash
flask run
```

## 📁 Project Structure

```
app/
├── config/        # Configuration
├── db/           # Database management
├── models/       # Data models
├── routes/       # Route handlers
├── static/       # Static assets
├── templates/    # HTML templates
├── utils/        # Utilities
└── app.py        # Application entry
```

## 🛠️ Development

Requirements:
- Python 3.9+
- PostgreSQL
- pip

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.