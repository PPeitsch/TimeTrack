from app.db.database import db
from app.models.models import AbsenceCode, Employee


def init_data():
    try:
        # Default employee
        if not Employee.query.get(1):
            default_user = Employee(id=1, name="Default User")
            db.session.add(default_user)

        # Absence codes
        codes = [
            "LAR",
            "FRANCO COMPENSATORIO",
            "LICENCIA MÉDICA",
            "COMISIÓN DE SERVICIO",
        ]
        for code in codes:
            if not AbsenceCode.query.filter_by(code=code).first():
                db.session.add(AbsenceCode(code=code))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
