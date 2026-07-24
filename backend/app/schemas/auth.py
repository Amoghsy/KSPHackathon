from pydantic import BaseModel
from typing import Any, Optional


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = "Investigator"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginOTPResponse(BaseModel):
    otp_required: bool = True
    challenge_id: str
    expires_in: int
    message: str


class VerifyOTPRequest(BaseModel):
    challenge_id: str
    otp: str


class VerifyOTPResponse(BaseModel):
    otp_required: bool = False
    access_token: str
    token_type: str = "bearer"
    session_id: str
    username: str
    role: str
    user: Optional[dict[str, Any]] = None


class ResendOTPRequest(BaseModel):
    challenge_id: str


class SessionOut(BaseModel):
    session_id: str
    device_name: str
    browser: str
    os: str
    device_type: str
    ip_address: str
    created_at: str
    last_activity_at: str
    is_current: bool


