from typing import List, Optional

from flask_sqlalchemy.model import Model
from sqlalchemy import JSON, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.db.database import db


# Esta clase de modelo sirve para tipar correctamente
class Base(Model):
    pass


# Actualiza las clases para usar el tipado correcto
class Employee(db.Model):  # type: ignore
    __tablename__ = "employees"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String)
    schedule_entries: Mapped[List["ScheduleEntry"]] = relationship(
        "ScheduleEntry", back_populates="employee"
    )


class ScheduleEntry(db.Model):  # type: ignore
    __tablename__ = "schedule_entries"
    id: int = Column(Integer, primary_key=True)
    employee_id: int = Column(Integer, ForeignKey("employees.id"))
    date: Date = Column(Date, nullable=False)
    entries: dict = Column(JSON, nullable=False)
    absence_code: Optional[str] = Column(String, nullable=True)
    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="schedule_entries"
    )


class Holiday(db.Model):  # type: ignore
    __tablename__ = "holidays"
    id: int = Column(Integer, primary_key=True)
    date: Date = Column(Date, unique=True, nullable=False)
    description: str = Column(String)
    type: str = Column(String)


class AbsenceCode(db.Model):  # type: ignore
    __tablename__ = "absence_codes"
    id: int = Column(Integer, primary_key=True)
    code: str = Column(String, unique=True, nullable=False)
    description: str = Column(String)
