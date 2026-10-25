from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.flag import ValidationFlagResponse


class StudentResponse(BaseModel):
    id: int
    college_id: int
    college_name: Optional[str] = None
    apaar_id: Optional[str] = None
    masked_apaar_id: str
    student_name: str
    programme: str
    academic_year: str
    admission_date: Optional[str] = None
    admission_category: Optional[str] = "General"
    source_batch_id: Optional[int] = None
    record_status: str  # valid, warning, invalid
    risk_score: float
    risk_level: str  # Low, Moderate, High, Critical
    anomaly_score: Optional[float] = None
    flags_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskScoreBreakdownItem(BaseModel):
    rule_code: str
    rule_name: str
    points: int
    severity: str
    description: str


class StudentDetailResponse(StudentResponse):
    flags: List[ValidationFlagResponse] = []
    risk_breakdown: List[RiskScoreBreakdownItem] = []
    has_registry_match: bool = False
    has_counselling_match: bool = False
    has_exam_record: bool = False
    has_fees_record: bool = False
    notes: Optional[str] = None
