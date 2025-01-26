from app.db.database import db


class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    schedule_entries = db.relationship("ScheduleEntry", back_populates="employee")


class ScheduleEntry(db.Model):
    __tablename__ = "schedule_entries"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"))
    date = db.Column(db.Date, nullable=False)
    entries = db.Column(db.JSON, nullable=False)
    absence_code = db.Column(db.String, nullable=True)
    employee = db.relationship("Employee", back_populates="schedule_entries")


class Holiday(db.Model):
    __tablename__ = "holidays"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    description = db.Column(db.String)
    type = db.Column(db.String)


class AbsenceCode(db.Model):
    __tablename__ = "absence_codes"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
