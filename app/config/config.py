import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/time_tracking')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')

    # Configuración horaria
    WORKING_HOURS_PER_DAY = 8
    WORKING_DAYS_PER_WEEK = 5

    # URLs
    HOLIDAYS_BASE_URL = "https://www.argentina.gob.ar/interior/feriados-nacionales-{year}"

    # Códigos de ausencia válidos
    ABSENCE_CODES = [
        'LAR',
        'FRANCO COMPENSATORIO',
        'LICENCIA MÉDICA',
        'COMISIÓN DE SERVICIO',
        'EXAMEN',
        'LICENCIA SIN GOCE'
    ]