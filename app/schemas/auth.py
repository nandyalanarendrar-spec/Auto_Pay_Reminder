from pydantic import BaseModel
from typing import Optional

class UserSignup(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    phone_number: Optional[str] = None  # Format: +919876543210 (E.164)

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: Optional[str] = None
    phone_number: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: Optional[str] = None
    new_password: str

