from pydantic import BaseModel


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

