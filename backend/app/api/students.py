from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.student import Student
from app.models.college import College
from app.models.validation_flag import ValidationFlag
from app.schemas.student import StudentResponse, StudentDetailResponse, RiskScoreBreakdownItem
from app.schemas.flag import ValidationFlagResponse
from app.core.security import mask_apaar_id
from app.core.permissions import get_current_user, enforce_college_tenant
from app.services.risk_service import calculate_risk_score
from app.services.registry_service import registry_service

router = APIRouter(prefix="/students", tags=["Students"])


def map_student_to_response(student: Student) -> StudentResponse:
    college_name = student.college.name if student.college else "Unknown"
    
    score = student.risk_score or 0.0
    if score < 20:
        level = "Low"
    elif score < 50:
        level = "Moderate"
    elif score < 75:
        level = "High"
    else:
        level = "Critical"

    return StudentResponse(
        id=student.id,
        college_id=student.college_id,
        college_name=college_name,
        apaar_id=student.apaar_id,
        masked_apaar_id=mask_apaar_id(student.apaar_id),
        student_name=student.student_name,
        programme=student.programme,
        academic_year=student.academic_year,
        admission_date=student.admission_date,
        admission_category=student.admission_category,
        source_batch_id=student.source_batch_id,
        record_status=student.record_status,
        risk_score=score,
        risk_level=level,
        anomaly_score=student.anomaly_score,
        flags_count=len(student.flags) if student.flags else 0,
        created_at=student.created_at
    )


@router.get("", response_model=List[StudentResponse])
def get_students(
    college_id: Optional[int] = Query(None),
    record_status: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    programme: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Enforce tenant isolation
    target_college_id = college_id
    if current_user.role == "college_admin":
        if target_college_id and target_college_id != current_user.college_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant isolation violation: Access denied to other college's records."
            )
        target_college_id = current_user.college_id

    query = db.query(Student)
    if target_college_id:
        query = query.filter(Student.college_id == target_college_id)

    if record_status and record_status != "all":
        query = query.filter(Student.record_status == record_status)

    if programme and programme != "all":
        query = query.filter(Student.programme.ilike(f"%{programme}%"))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (Student.student_name.ilike(search_term)) |
            (Student.apaar_id.ilike(search_term)) |
            (Student.programme.ilike(search_term))
        )

    students = query.order_by(Student.id.desc()).offset(offset).limit(limit).all()
    return [map_student_to_response(s) for s in students]


@router.get("/{student_id}", response_model=StudentDetailResponse)
def get_student_detail(student_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Tenant check
    enforce_college_tenant(current_user, student.college_id)

    base_resp = map_student_to_response(student)

    # Collect flags
    flags = db.query(ValidationFlag).filter(ValidationFlag.student_id == student.id).all()
    flag_responses = [
        ValidationFlagResponse(
            id=f.id,
            student_id=f.student_id,
            batch_id=f.batch_id,
            row_index=f.row_index,
            rule_code=f.rule_code,
            severity=f.severity,
            explanation=f.explanation,
            suggested_action=f.suggested_action,
            status=f.status,
            review_notes=f.review_notes,
            created_at=f.created_at,
            updated_at=f.updated_at
        )
        for f in flags
    ]

    rule_codes = [f.rule_code for f in flags]
    _, _, breakdown = calculate_risk_score(rule_codes)
    risk_breakdown = [RiskScoreBreakdownItem(**b) for b in breakdown]

    # Check synthetic external matches
    apaar = student.apaar_id or ""
    has_reg = bool(registry_service.lookup_apaar_registry(apaar)) if apaar else False
    has_couns = bool(registry_service.lookup_counselling_record(apaar)) if apaar else False
    has_ex = bool(registry_service.lookup_exam_record(apaar)) if apaar else False
    has_fe = bool(registry_service.lookup_fee_record(apaar)) if apaar else False

    return StudentDetailResponse(
        **base_resp.model_dump(),
        flags=flag_responses,
        risk_breakdown=risk_breakdown,
        has_registry_match=has_reg,
        has_counselling_match=has_couns,
        has_exam_record=has_ex,
        has_fees_record=has_fe
    )


@router.get("/{student_id}/flags", response_model=List[ValidationFlagResponse])
def get_student_flags(student_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    enforce_college_tenant(current_user, student.college_id)

    flags = db.query(ValidationFlag).filter(ValidationFlag.student_id == student.id).all()
    return [
        ValidationFlagResponse(
            id=f.id,
            student_id=f.student_id,
            batch_id=f.batch_id,
            row_index=f.row_index,
            rule_code=f.rule_code,
            severity=f.severity,
            explanation=f.explanation,
            suggested_action=f.suggested_action,
            status=f.status,
            review_notes=f.review_notes,
            created_at=f.created_at,
            updated_at=f.updated_at
        )
        for f in flags
    ]
