from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from app.database.session import get_db
from app.models.college import College
from app.models.student import Student
from app.models.validation_flag import ValidationFlag
from app.schemas.compliance import (
    ComplianceSummaryResponse,
    RiskDistributionItem,
    OverIntakeInstitution,
    CrossCollegeDuplicateGroup
)
from app.schemas.flag import ValidationFlagResponse, FlagUpdateStatusRequest
from app.core.permissions import get_current_user, require_role
from app.core.security import mask_apaar_id
from app.services.intake_service import get_college_intake_status
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="", tags=["Compliance & Oversight"])


@router.get("/compliance/summary", response_model=ComplianceSummaryResponse)
def get_compliance_summary(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    colleges = db.query(College).filter(College.is_active == True).all()
    students = db.query(Student).all()
    flags = db.query(ValidationFlag).all()

    total_inst = len(colleges)
    total_stud = len(students)
    valid_count = sum(1 for s in students if s.record_status == "valid")
    warn_count = sum(1 for s in students if s.record_status == "warning")
    inv_count = sum(1 for s in students if s.record_status == "invalid")

    # Over intake institutions
    over_intake_list = []
    total_utilization = 0.0
    for c in colleges:
        status_info = get_college_intake_status(db, c.id)
        total_utilization += status_info["utilization_rate"]
        if status_info["is_over_intake"]:
            over_intake_list.append(OverIntakeInstitution(
                college_id=c.id,
                college_name=c.name,
                institution_code=c.institution_code,
                approved_intake=status_info["approved_intake"],
                admitted_count=status_info["current_enrolled"],
                over_intake_count=status_info["over_intake_count"],
                utilization_rate=status_info["utilization_rate"]
            ))

    avg_util = round(total_utilization / total_inst, 1) if total_inst > 0 else 0.0

    # Cross college duplicates
    # Group students by apaar_id where distinct college_id > 1
    apaar_map = {}
    for s in students:
        if s.apaar_id:
            apaar_map.setdefault(s.apaar_id, []).append(s)

    cross_duplicates = []
    for apaar, s_list in apaar_map.items():
        distinct_colleges = {s.college_id for s in s_list}
        if len(distinct_colleges) > 1:
            college_entries = []
            for s in s_list:
                college_entries.append({
                    "college_id": s.college_id,
                    "college_name": s.college.name if s.college else "Unknown",
                    "programme": s.programme,
                    "admission_date": s.admission_date
                })
            cross_duplicates.append(CrossCollegeDuplicateGroup(
                apaar_id=apaar,
                masked_apaar_id=mask_apaar_id(apaar),
                student_name=s_list[0].student_name,
                colleges=college_entries
            ))

    # Risk distribution
    low_cnt = sum(1 for s in students if (s.risk_score or 0) < 20)
    mod_cnt = sum(1 for s in students if 20 <= (s.risk_score or 0) < 50)
    high_cnt = sum(1 for s in students if 50 <= (s.risk_score or 0) < 75)
    crit_cnt = sum(1 for s in students if (s.risk_score or 0) >= 75)

    denom = max(1, total_stud)
    risk_distribution = [
        RiskDistributionItem(category="Low (0-19)", count=low_cnt, percentage=round(low_cnt / denom * 100, 1), color="#10B981"),
        RiskDistributionItem(category="Moderate (20-49)", count=mod_cnt, percentage=round(mod_cnt / denom * 100, 1), color="#F59E0B"),
        RiskDistributionItem(category="High (50-74)", count=high_cnt, percentage=round(high_cnt / denom * 100, 1), color="#F97316"),
        RiskDistributionItem(category="Critical (75-100)", count=crit_cnt, percentage=round(crit_cnt / denom * 100, 1), color="#EF4444")
    ]

    total_f = len(flags)
    open_f = sum(1 for f in flags if f.status == "open")
    res_f = sum(1 for f in flags if f.status in ["resolved", "false_positive"])

    return ComplianceSummaryResponse(
        total_institutions=total_inst,
        total_students=total_stud,
        valid_records=valid_count,
        warning_records=warn_count,
        invalid_records=inv_count,
        potential_cross_college_duplicates=len(cross_duplicates),
        institutions_exceeding_intake=len(over_intake_list),
        average_utilization_rate=avg_util,
        total_flags=total_f,
        open_flags=open_f,
        resolved_flags=res_f,
        risk_distribution=risk_distribution,
        over_intake_institutions=over_intake_list,
        cross_college_duplicates=cross_duplicates
    )


@router.get("/compliance/risk-distribution")
def get_risk_distribution(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    summary = get_compliance_summary(db, current_user)
    return summary.risk_distribution


@router.get("/compliance/over-intake")
def get_over_intake(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    summary = get_compliance_summary(db, current_user)
    return summary.over_intake_institutions


@router.patch("/flags/{flag_id}", response_model=ValidationFlagResponse)
def update_flag_status(
    flag_id: int,
    payload: FlagUpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    flag = db.query(ValidationFlag).filter(ValidationFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation flag not found")

    old_status = flag.status
    flag.status = payload.status
    if payload.review_notes:
        flag.review_notes = payload.review_notes
    db.commit()
    db.refresh(flag)

    log_audit_event(
        db=db,
        action="FLAG_STATUS_CHANGE",
        entity_type="VALIDATION_FLAG",
        entity_id=str(flag.id),
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        college_id=flag.student.college_id if flag.student else None,
        metadata={
            "flag_id": flag.id,
            "rule_code": flag.rule_code,
            "old_status": old_status,
            "new_status": flag.status,
            "review_notes": payload.review_notes
        }
    )

    return ValidationFlagResponse(
        id=flag.id,
        student_id=flag.student_id,
        batch_id=flag.batch_id,
        row_index=flag.row_index,
        rule_code=flag.rule_code,
        severity=flag.severity,
        explanation=flag.explanation,
        suggested_action=flag.suggested_action,
        status=flag.status,
        review_notes=flag.review_notes,
        created_at=flag.created_at,
        updated_at=flag.updated_at
    )
