from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ValidationFlagResponse(BaseModel):
    id: int
    student_id: Optional[int] = None
    batch_id: int
    row_index: Optional[int] = None
    rule_code: str
    severity: str
    explanation: str
    suggested_action: Optional[str] = None
    status: str
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FlagUpdateStatusRequest(BaseModel):
    status: str  # open, under_review, resolved, false_positive
    review_notes: Optional[str] = None
