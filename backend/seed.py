from database import SessionLocal, engine, Base
from models import Employee, Payslip
import bcrypt

# Create all tables in the DB
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

# Sample Employees
employees = [
    Employee(
        employee_id   = "EMP001",
        name          = "Ravi Sharma",
        department    = "Engineering",
        designation   = "Software Engineer",
        email         = "ravi@company.com",
        password_hash = hash_password("pass1234"),
        esi_no        = None,
        uan           = None,
    ),
    Employee(
        employee_id   = "EMP002",
        name          = "Priya Mehta",
        department    = "Human Resources",
        designation   = "HR Manager",
        email         = "priya@company.com",
        password_hash = hash_password("mypassword"),
        esi_no        = None,
        uan           = None,
    ),
]

# Sample Payslips — ✅ FIXED: uses new field names matching models.py
payslips = [
    Payslip(
        employee_id     = "EMP001",
        month           = "January",
        year            = 2025,
        paid_days       = 26,
        basic           = 50000,
        bonus           = 4000,
        shift_allowance = 2000,
        incentive       = 2500,
        lww             = 1500,
        pf              = 6000,
        esic            = 0,
        lwf             = 10,
        transport       = 750,
        gross_salary    = 60000,
        total_deduction = 6760,
        net_salary      = 53240,
    ),
    Payslip(
        employee_id     = "EMP002",
        month           = "January",
        year            = 2025,
        paid_days       = 25,
        basic           = 70000,
        bonus           = 5000,
        shift_allowance = 3000,
        incentive       = 3500,
        lww             = 2000,
        pf              = 8400,
        esic            = 0,
        lwf             = 10,
        transport       = 750,
        gross_salary    = 83500,
        total_deduction = 9160,
        net_salary      = 74340,
    ),
]

db.add_all(employees)
db.add_all(payslips)
db.commit()
db.close()

print("✅ Database seeded successfully!")
