from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class CertificateIssueRequest(BaseModel):
    student_id: int
    expiry_months: int = 12


class CertificateResponse(BaseModel):
    id: int
    certificate_reference: str
    student_id: int
    student_name: str
    college_name: str
    programme: str
    academic_year: str
    canonical_payload: str
    digital_signature: str
    signature_algorithm: str
    qr_code_data_uri: str
    verification_url: str
    issued_at: datetime
    expires_at: datetime
    is_revoked: bool
    revocation_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CertificateVerifyResponse(BaseModel):
    is_valid: bool
    status: str  # VALID, EXPIRED, REVOKED, INVALID_SIGNATURE, NOT_FOUND
    message: str
    certificate_reference: Optional[str] = None
    institution: Optional[str] = None
    programme: Optional[str] = None
    student_reference: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    digital_signature_verified: bool = False
