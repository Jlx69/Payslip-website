from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

import pandas as pd
import bcrypt
import io

from database import engine, get_db, Base
from models import Employee, Payslip
from schemas import LoginRequest, LoginResponse, EmployeeProfile, PayslipInfo
from auth import verify_password, create_access_token, decode_token
from pdf_generator import generate_payslip_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payslip Generator API")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jlx69.github.io",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# 🔧 Helper: Detect company from employee ID
# ─────────────────────────────────────────
def detect_company(emp_id: str) -> str:
    """
    MES-xxx → Commscope
    ME-xxx  → Andrew
    Check MES- FIRST (longer prefix takes priority)
    """
    if emp_id.upper().startswith("MES-"):
        return "Commscope"
    elif emp_id.upper().startswith("ME-"):
        return "Andrew"
    else:
        return "Andrew"  # default


# ─────────────────────────────────────────
# 🔧 Helper: Extract employee from token
# ─────────────────────────────────────────
def get_current_employee(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Employee:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    employee = db.query(Employee).filter(
        Employee.employee_id == payload.get("sub")
    ).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    return employee


# ─────────────────────────────────────────
# 🏥 GET / — Health check
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Payslip API is running ✅"}


# ─────────────────────────────────────────
# 🔐 POST /login — Employee login
# ─────────────────────────────────────────
@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(
        Employee.employee_id == request.employee_id
    ).first()
    if not employee or not verify_password(request.password, employee.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Employee ID or password")
    token = create_access_token(data={"sub": employee.employee_id})
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        employee_name=employee.name,
        employee_id=employee.employee_id
    )


# ─────────────────────────────────────────
# 👤 GET /me — Get logged-in employee profile
# ─────────────────────────────────────────
@app.get("/me", response_model=EmployeeProfile)
def get_profile(current_employee: Employee = Depends(get_current_employee)):
    return current_employee


# ─────────────────────────────────────────
# 📋 GET /payslips — List payslips
# ─────────────────────────────────────────
@app.get("/payslips")
def get_payslips(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    payslips = db.query(Payslip).filter(
        Payslip.employee_id == current_employee.employee_id
    ).all()
    if not payslips:
        raise HTTPException(status_code=404, detail="No payslips found")
    return [
        {"id": p.id, "month": p.month, "year": p.year, "net_salary": p.net_salary}
        for p in payslips
    ]


# ─────────────────────────────────────────
# 📥 GET /payslips/{id}/download — Generate PDF
# ─────────────────────────────────────────
@app.get("/payslips/{payslip_id}/download")
def download_payslip(
    payslip_id: int,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if payslip.employee_id != current_employee.employee_id:
        raise HTTPException(status_code=403, detail="Access denied")

    employee_data = {
        "employee_id": current_employee.employee_id,
        "name":        current_employee.name,
        "department":  current_employee.department,
        "esi_no":      current_employee.esi_no,
        "uan":         current_employee.uan,
        "company":     current_employee.company,
    }
    payslip_data = {
        "month":           payslip.month,
        "year":            payslip.year,
        "paid_days":       payslip.paid_days,
        "basic":           payslip.basic,
        "bonus":           payslip.bonus,
        "shift_allowance": payslip.shift_allowance,
        "incentive":       payslip.incentive,
        "lww":             payslip.lww,
        "pf":              payslip.pf,
        "esic":            payslip.esic,
        "lwf":             payslip.lwf,
        "transport":       payslip.transport,
        "gross_salary":    payslip.gross_salary,
        "total_deduction": payslip.total_deduction,
        "net_salary":      payslip.net_salary,
    }

    pdf_bytes = generate_payslip_pdf(employee_data, payslip_data)
    filename  = f"Payslip_{current_employee.employee_id}_{payslip.month}_{payslip.year}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ─────────────────────────────────────────
# 🔐 POST /admin/login
# ─────────────────────────────────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.post("/admin/login")
def admin_login(request: LoginRequest):
    if request.employee_id != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    token = create_access_token(data={"sub": "admin", "role": "admin"})
    return {"access_token": token, "token_type": "bearer"}


# ─────────────────────────────────────────
# 📤 POST /admin/upload — Upload monthly wage Excel
# ─────────────────────────────────────────
@app.post("/admin/upload")
async def upload_wagesheet(
    file: UploadFile = File(...),
    month: str = "March",
    year: int = 2026,
    company: str = "Andrew",   # ✅ "Andrew" or "Commscope"
    db: Session = Depends(get_db)
):
    contents = await file.read()

    try:
        df = pd.read_excel(io.BytesIO(contents), sheet_name="main attendance", header=3)
    except Exception:
        df = pd.read_excel(io.BytesIO(contents), sheet_name=0, header=3)

    df.columns = df.columns.str.strip()

    inserted = 0
    updated  = 0
    errors   = []

    def safe_float(val):
        try:
            v = float(val)
            return 0.0 if pd.isna(v) else v
        except:
            return 0.0

    def safe_str(val):
        s = str(val).strip()
        return None if s in ("", "nan", "None", "NaT") else s

    for _, row in df.iterrows():
        try:
            emp_code = safe_str(row.get("Emp Code", ""))
            emp_name = safe_str(row.get("Emp Name", ""))
            if not emp_code or emp_code == "Emp Code":
                continue

            # ── Auto-detect company from emp ID ──────────────────
            emp_company = detect_company(emp_code)

            # ── Upsert Employee ───────────────────────────────────
            employee = db.query(Employee).filter(
                Employee.employee_id == emp_code
            ).first()

            if not employee:
                default_password = bcrypt.hashpw(
                    emp_code.encode(), bcrypt.gensalt()
                ).decode()
                employee = Employee(
                    employee_id   = emp_code,
                    name          = emp_name,
                    department    = safe_str(row.get("Department Name", "")) or "",
                    designation   = "",
                    email         = "",
                    password_hash = default_password,
                    esi_no        = None,
                    uan           = None,
                    company       = emp_company,  # ✅ auto-detected
                )
                db.add(employee)
            else:
                employee.name       = emp_name
                employee.department = safe_str(row.get("Department Name", "")) or ""
                employee.company    = emp_company  # ✅ update on re-upload

            # ── Parse salary fields ───────────────────────────────
            paid_days       = safe_float(row.get("Paid days in a month"))
            basic           = safe_float(row.get("Basic"))
            bonus           = safe_float(row.get("Bonus"))
            shift_allowance = safe_float(row.get("Total Shift Allowance Amount"))
            incentive       = safe_float(row.get("Monthly Attendance Incentive"))
            lww             = safe_float(row.get("LWW"))
            pf              = safe_float(row.get("PF @12%"))
            esic            = safe_float(row.get("ESIC @0.75%"))
            lwf             = safe_float(row.get("LWF"))
            transport       = safe_float(row.get("Transport Facility Chrges"))
            gross_salary    = safe_float(row.get("Gross Salary"))
            total_deduction = safe_float(row.get("Total Deduction"))
            net_salary      = safe_float(row.get("Net Salary"))

            # ── Upsert Payslip ────────────────────────────────────
            existing_slip = db.query(Payslip).filter(
                Payslip.employee_id == emp_code,
                Payslip.month       == month,
                Payslip.year        == year
            ).first()

            if existing_slip:
                existing_slip.paid_days       = paid_days
                existing_slip.basic           = basic
                existing_slip.bonus           = bonus
                existing_slip.shift_allowance = shift_allowance
                existing_slip.incentive       = incentive
                existing_slip.lww             = lww
                existing_slip.pf              = pf
                existing_slip.esic            = esic
                existing_slip.lwf             = lwf
                existing_slip.transport       = transport
                existing_slip.gross_salary    = gross_salary
                existing_slip.total_deduction = total_deduction
                existing_slip.net_salary      = net_salary
                existing_slip.company         = emp_company  # ✅
                updated += 1
            else:
                slip = Payslip(
                    employee_id     = emp_code,
                    month           = month,
                    year            = year,
                    company         = emp_company,  # ✅
                    paid_days       = paid_days,
                    basic           = basic,
                    bonus           = bonus,
                    shift_allowance = shift_allowance,
                    incentive       = incentive,
                    lww             = lww,
                    pf              = pf,
                    esic            = esic,
                    lwf             = lwf,
                    transport       = transport,
                    gross_salary    = gross_salary,
                    total_deduction = total_deduction,
                    net_salary      = net_salary,
                )
                db.add(slip)
                inserted += 1

        except Exception as e:
            errors.append(f"Row error ({row.get('Emp Code', '?')}): {str(e)}")

    db.commit()
    return {"message": "Upload complete", "inserted": inserted, "updated": updated, "errors": errors}


# ─────────────────────────────────────────
# 🪪 POST /admin/upload-uan-esic
# ─────────────────────────────────────────
@app.post("/admin/upload-uan-esic")
async def upload_uan_esic(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(contents), sheet_name=0, header=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    df.columns = df.columns.str.strip()

    updated   = 0
    not_found = []
    errors    = []

    def safe_id_str(val):
        try:
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            return str(int(float(val)))
        except:
            s = str(val).strip()
            return None if s in ("", "nan", "None") else s

    for _, row in df.iterrows():
        try:
            emp_id = str(row.get("Emp ID", "")).strip()
            uan    = safe_id_str(row.get("UAN No."))
            esi_no = safe_id_str(row.get("E.S.I. No."))
            if not emp_id or emp_id == "nan":
                continue
            employee = db.query(Employee).filter(
                Employee.employee_id == emp_id
            ).first()
            if not employee:
                not_found.append(emp_id)
                continue
            if uan:    employee.uan    = uan
            if esi_no: employee.esi_no = esi_no
            updated += 1
        except Exception as e:
            errors.append(f"Row error ({row.get('Emp ID', '?')}): {str(e)}")

    db.commit()
    return {"message": "UAN/ESIC upload complete", "updated": updated, "not_found": not_found, "errors": errors}


# ─────────────────────────────────────────
# 👥 GET /admin/employees — List all employees
# ─────────────────────────────────────────
@app.get("/admin/employees")
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).order_by(Employee.company, Employee.employee_id).all()
    return [
        {
            "employee_id": e.employee_id,
            "name":        e.name,
            "department":  e.department,
            "esi_no":      e.esi_no or "—",
            "uan":         e.uan    or "—",
            "company":     e.company or "Andrew",
        }
        for e in employees
    ]
