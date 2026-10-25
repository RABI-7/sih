from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class VerificationRequestCreate(BaseModel):
    student_identifier: str  # Student ID or APAAR ID or reference
    purpose: str
    verifier_name: Optional[str] = "Academic Background Verification Agency"


class ConsentGrantRequest(BaseModel):
    permitted_fields: List[str]  # e.g., ["student_name", "programme", "college_name", "academic_year", "admission_category"]
    duration_days: int = 7


class VerificationRequestResponse(BaseModel):
    id: int
    request_reference: str
    student_id: int
    student_name: str
    masked_apaar_id: str
    purpose: str
    verifier_name: str
    status: str
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationResultResponse(BaseModel):
    request_reference: str
    status: str  # consent_granted, pending_consent, expired, revoked
    purpose: str
    verifier_name: str
    is_valid_access: bool
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    permitted_fields: List[str] = []
    student_data: Dict[str, Any] = {}
    message: Optional[str] = None
