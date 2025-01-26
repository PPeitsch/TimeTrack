from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    schedule_entries = relationship("ScheduleEntry", back_populates="employee")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(Date, nullable=False)
    entries = Column(JSON, nullable=False)
    absence_code = Column(String, nullable=True)
    employee = relationship("Employee", back_populates="schedule_entries")


class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    description = Column(String)
    type = Column(String)  # Inamovible, Trasladable, etc


class AbsenceCode(Base):
    __tablename__ = "absence_codes"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String)
