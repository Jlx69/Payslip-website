from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base

class Employee(Base):
    __tablename__ = "employees"

    id            = Column(Integer, primary_key=True, index=True)
    employee_id   = Column(String, unique=True, index=True)  # Emp Code e.g. ME-1903
    name          = Column(String)
    department    = Column(String)
    designation   = Column(String, nullable=True)
    email         = Column(String, nullable=True)
    password_hash = Column(String)
    esi_no        = Column(String, nullable=True)   # Empty for now
    uan           = Column(String, nullable=True)   # Empty for now


class Payslip(Base):
    __tablename__ = "payslips"

    id               = Column(Integer, primary_key=True, index=True)
    employee_id      = Column(String, ForeignKey("employees.employee_id"))
    month            = Column(String)    # e.g. "March"
    year             = Column(Integer)   # e.g. 2026

    # Attendance
    paid_days        = Column(Float)

    # Earnings
    basic            = Column(Float)
    bonus            = Column(Float)
    shift_allowance  = Column(Float)
    incentive        = Column(Float)
    lww              = Column(Float)

    # Deductions
    pf               = Column(Float)
    esic             = Column(Float, default=0)   # Empty for now
    lwf              = Column(Float)
    transport        = Column(Float)

    # Totals
    gross_salary     = Column(Float)
    total_deduction  = Column(Float)
    net_salary       = Column(Float)