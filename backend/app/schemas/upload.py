from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime


class UploadBatchResponse(BaseModel):
    id: int
    college_id: int
    college_name: Optional[str] = None
    filename: str
    file_sha256: str
    upload_timestamp: datetime
    uploaded_by: Optional[int] = None
    uploader_name: Optional[str] = None
    processing_status: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    warning_rows: int
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RowValidationDetail(BaseModel):
    row_number: int
    apaar_id_raw: Optional[str] = None
    masked_apaar_id: str
    student_name: str
    programme: str
    academic_year: str
    admission_date: Optional[str] = None
    admission_category: Optional[str] = None
    status: str  # valid, warning, invalid
    primary_issue: Optional[str] = None
    recommended_action: Optional[str] = None
    triggered_rules: List[str] = []
    flags: List[Dict[str, Any]] = []


class UploadBatchResultResponse(BaseModel):
    batch: UploadBatchResponse
    total_records: int
    valid_count: int
    warning_count: int
    invalid_count: int
    rows: List[RowValidationDetail]
