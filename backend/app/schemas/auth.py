from pydantic import BaseModel, ConfigDict
from typing import Optional


class DemoLoginRequest(BaseModel):
    account_key: str  # college_admin_1, college_admin_2, compliance_officer, verifier


class VerifyOtpRequest(BaseModel):
    account_key: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    college_id: Optional[int] = None
    college_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


TokenResponse.model_rebuild()
