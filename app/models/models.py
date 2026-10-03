from typing import List

from flask_login import UserMixin  # type: ignore
from sqlalchemy import JSON, Column
from sqlalchemy import Date as SQLADate
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.db.database import db


class Employee(UserMixin, db.Model):  # type: ignore
    """The person whose hours are tracked; also the account that logs in."""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)

    schedule_entries: Mapped[List["ScheduleEntry"]] = relationship(
        "ScheduleEntry", back_populates="employee"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)  # type: ignore[assignment]

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(str(self.password_hash), password)


class ScheduleEntry(db.Model):  # type: ignore
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(SQLADate, nullable=False)
    entries = Column(JSON, nullable=False)
    absence_code = Column(String, nullable=True)
    observation = Column(String, nullable=True)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="schedule_entries"
    )


class Holiday(db.Model):  # type: ignore
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True)
    date = Column(SQLADate, unique=True, nullable=False)
    description = Column(String)
    type = Column(String)


class AbsenceCode(db.Model):  # type: ignore
    __tablename__ = "absence_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String)
