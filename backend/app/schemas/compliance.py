from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.schemas.college import CollegeResponse


class RiskDistributionItem(BaseModel):
    category: str  # Low, Moderate, High, Critical
    count: int
    percentage: float
    color: str


class OverIntakeInstitution(BaseModel):
    college_id: int
    college_name: str
    institution_code: str
    approved_intake: int
    admitted_count: int
    over_intake_count: int
    utilization_rate: float


class CrossCollegeDuplicateGroup(BaseModel):
    apaar_id: str
    masked_apaar_id: str
    student_name: str
    colleges: List[Dict[str, Any]]  # college_id, college_name, programme, admission_date


class ComplianceSummaryResponse(BaseModel):
    total_institutions: int
    total_students: int
    valid_records: int
    warning_records: int
    invalid_records: int
    potential_cross_college_duplicates: int
    institutions_exceeding_intake: int
    average_utilization_rate: float
    total_flags: int
    open_flags: int
    resolved_flags: int
    risk_distribution: List[RiskDistributionItem]
    over_intake_institutions: List[OverIntakeInstitution]
    cross_college_duplicates: List[CrossCollegeDuplicateGroup]
