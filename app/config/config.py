import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://user:pass@localhost:5432/timetrack"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")

    # Holiday provider configuration
    HOLIDAY_PROVIDER = os.getenv("HOLIDAY_PROVIDER", "ARGENTINA_WEBSITE")
    HOLIDAYS_BASE_URL = os.getenv(
        "HOLIDAYS_BASE_URL",
        "https://www.argentina.gob.ar/interior/feriados-nacionales-{year}",
    )

    # Configuración horaria
    WORKING_HOURS_PER_DAY = 8
    WORKING_DAYS_PER_WEEK = 5
