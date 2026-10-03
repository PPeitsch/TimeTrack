import os

from dotenv import load_dotenv

# Load .env so `python run.py` and `init_db.py` see the same settings as `flask run`.
load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://user:pass@localhost:5432/timetrack"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Required outside debug/testing; create_app refuses to start without it.
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Session cookies (set SESSION_COOKIE_SECURE=true behind HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    # Login
    LOGIN_MAX_ATTEMPTS = 10
    LOGIN_RATE_WINDOW_SECONDS = 15 * 60
    # Demo mode: show the demo credentials on the login page.
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
    DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo")

    # Uploads (file import)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    UPLOAD_MAX_AGE_HOURS = 24

    # Holiday provider configuration
    # ISO 3166-1 alpha-2 code of the country whose public holidays are loaded.
    HOLIDAY_COUNTRY = os.getenv("HOLIDAY_COUNTRY", "AR").strip().upper()
    # Without an explicit provider, Argentina uses ArgentinaDatos (it also lists
    # the bridge days that Nager.Date omits) and every other country Nager.Date.
    HOLIDAY_PROVIDER = os.getenv("HOLIDAY_PROVIDER") or (
        "ARGENTINA_API" if HOLIDAY_COUNTRY == "AR" else "NAGER_DATE"
    )
    HOLIDAYS_BASE_URL = os.getenv(
        "HOLIDAYS_BASE_URL",
        "https://www.argentina.gob.ar/jefatura/feriados-nacionales-{year}",
    )
    HOLIDAY_API_URL = os.getenv(
        "HOLIDAY_API_URL",
        "https://api.argentinadatos.com/v1/feriados/{year}",
    )
    NAGER_DATE_API_URL = os.getenv(
        "NAGER_DATE_API_URL",
        "https://date.nager.at/api/v3/PublicHolidays/{year}/{country}",
    )

    # Load a year's holidays from the provider the first time it is viewed.
    HOLIDAY_AUTO_FETCH = os.getenv("HOLIDAY_AUTO_FETCH", "true").lower() == "true"

    # Configuración horaria
    WORKING_HOURS_PER_DAY = float(os.getenv("WORKING_HOURS_PER_DAY", "8"))
    WORKING_DAYS_PER_WEEK = 5
