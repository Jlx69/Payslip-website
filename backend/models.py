from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base


class Employee(Base):
    __tablename__ = "employees"

    id            = Column(Integer, primary_key=True, index=True)
    employee_id   = Column(String, unique=True, index=True)
    name          = Column(String)
    department    = Column(String)
    designation   = Column(String, nullable=True)
    email         = Column(String, nullable=True)
    password_hash = Column(String)
    esi_no        = Column(String, nullable=True)
    uan           = Column(String, nullable=True)
    company       = Column(String, default="Andrew")
    doj           = Column(String, nullable=True)   # Date of Joining (col D)


class Payslip(Base):
    __tablename__ = "payslips"

    id               = Column(Integer, primary_key=True, index=True)
    employee_id      = Column(String, ForeignKey("employees.employee_id"))
    month            = Column(String)
    year             = Column(Integer)
    company          = Column(String, default="Andrew")
    paid_days        = Column(Float)
    basic            = Column(Float)
    bonus            = Column(Float)
    shift_allowance  = Column(Float)
    incentive        = Column(Float)
    lww              = Column(Float)
    pf               = Column(Float)
    esic             = Column(Float, default=0)
    lwf              = Column(Float)
    transport        = Column(Float)
    gross_salary     = Column(Float)
    total_deduction  = Column(Float)
    net_salary       = Column(Float)
