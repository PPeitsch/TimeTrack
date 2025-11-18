from app.db.database import db
from app.models.models import AbsenceCode, Employee

DEFAULT_ABSENCE_CODES = [
    "Compensatory Time",
    "Off-site Duty",
    "Personal Leave",
    "Sick Leave",
    "Study Leave",
    "Unpaid Leave",
    "Vacation",
]


def init_data():
    try:
        # Default employee
        if not Employee.query.get(1):
            default_user = Employee(id=1, name="Default User")
            db.session.add(default_user)

        # Absence codes
        for code in DEFAULT_ABSENCE_CODES:
            if not AbsenceCode.query.filter_by(code=code).first():
                db.session.add(AbsenceCode(code=code))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
