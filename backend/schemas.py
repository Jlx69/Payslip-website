from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    employee_id: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    employee_name: str
    employee_id: str

class EmployeeProfile(BaseModel):
    employee_id: str
    name: str
    department: str
    designation: Optional[str] = None
    email: Optional[str] = None
    esi_no: Optional[str] = None
    uan: Optional[str] = None

class PayslipInfo(BaseModel):
    id: int
    month: str
    year: int
    net_salary: float

    class Config:
        from_attributes = True