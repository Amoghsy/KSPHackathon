from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    employee_id: str
    role: str = "Investigator"
    full_name: Optional[str] = ""
    password: Optional[str] = None
    districts: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str]
    employee_id: Optional[str]
    account_status: str

    class Config:
        from_attributes = True


class ActivateAccountPayload(BaseModel):
    token: str
    password: str

