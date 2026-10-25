from pydantic import BaseModel, ConfigDict
from typing import Optional


class CollegeResponse(BaseModel):
    id: int
    name: str
    institution_code: str
    approved_intake: int
    category: str
    state: str
    is_active: bool
    enrolled_count: Optional[int] = 0
    utilization_rate: Optional[float] = 0.0
    status: Optional[str] = "Normal"  # Normal, Near Capacity, Over-Intake

    model_config = ConfigDict(from_attributes=True)


class CollegeComplianceResponse(BaseModel):
    college: CollegeResponse
    total_students: int
    valid_students: int
    flagged_students: int
    approved_intake: int
    utilization_rate: float
    is_over_intake: bool
    over_intake_count: int
    critical_flags_count: int
