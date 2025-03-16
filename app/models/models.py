from datetime import date
from typing import Any, Dict, List, Optional, cast

from sqlalchemy import JSON, Column
from sqlalchemy import Date as SQLADate
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.db.database import db


class Employee(db.Model):  # type: ignore
    __tablename__ = "employees"

    # Usar = Column(...) para mypy, pero sin anotaciones de tipo
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # Esta es la única anotación que mantenemos con tipo
    schedule_entries: Mapped[List["ScheduleEntry"]] = relationship(
        "ScheduleEntry", back_populates="employee"
    )


class ScheduleEntry(db.Model):  # type: ignore
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(SQLADate, nullable=False)
    entries = Column(JSON, nullable=False)
    absence_code = Column(String, nullable=True)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="schedule_entries"
    )

    # Método para acceder a la fecha como objeto date de Python
    @property
    def date_obj(self) -> date:
        return cast(date, self.date)


class Holiday(db.Model):  # type: ignore
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True)
    date = Column(SQLADate, unique=True, nullable=False)
    description = Column(String)
    type = Column(String)

    # Método para acceder a la fecha como objeto date de Python
    @property
    def date_obj(self) -> date:
        return cast(date, self.date)


class AbsenceCode(db.Model):  # type: ignore
    __tablename__ = "absence_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String)
