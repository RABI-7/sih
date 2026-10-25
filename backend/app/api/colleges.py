from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.college import College
from app.models.student import Student
from app.schemas.college import CollegeResponse, CollegeComplianceResponse
from app.services.intake_service import get_college_intake_status
from app.core.permissions import get_current_user

router = APIRouter(prefix="/colleges", tags=["Colleges"])


@router.get("", response_model=List[CollegeResponse])
def get_colleges(db: Session = Depends(get_db)):
    colleges = db.query(College).filter(College.is_active == True).all()
    results = []
    for c in colleges:
        intake_info = get_college_intake_status(db, c.id)
        status_label = "Normal"
        if intake_info["is_over_intake"]:
            status_label = "Over-Intake"
        elif intake_info["utilization_rate"] >= 90.0:
            status_label = "Near Capacity"

        results.append(CollegeResponse(
            id=c.id,
            name=c.name,
            institution_code=c.institution_code,
            approved_intake=c.approved_intake,
            category=c.category,
            state=c.state,
            is_active=c.is_active,
            enrolled_count=intake_info["current_enrolled"],
            utilization_rate=intake_info["utilization_rate"],
            status=status_label
        ))
    return results


@router.get("/{college_id}/compliance", response_model=CollegeComplianceResponse)
def get_college_compliance(college_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    college = db.query(College).filter(College.id == college_id).first()
    if not college:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found")

    intake_info = get_college_intake_status(db, college_id)
    students = db.query(Student).filter(Student.college_id == college_id).all()
    
    total = len(students)
    valid = sum(1 for s in students if s.record_status == "valid")
    flagged = total - valid
    critical_count = sum(1 for s in students if s.record_status == "invalid")

    status_label = "Over-Intake" if intake_info["is_over_intake"] else ("Near Capacity" if intake_info["utilization_rate"] >= 90 else "Normal")
    college_resp = CollegeResponse(
        id=college.id,
        name=college.name,
        institution_code=college.institution_code,
        approved_intake=college.approved_intake,
        category=college.category,
        state=college.state,
        is_active=college.is_active,
        enrolled_count=intake_info["current_enrolled"],
        utilization_rate=intake_info["utilization_rate"],
        status=status_label
    )

    return CollegeComplianceResponse(
        college=college_resp,
        total_students=total,
        valid_students=valid,
        flagged_students=flagged,
        approved_intake=college.approved_intake,
        utilization_rate=intake_info["utilization_rate"],
        is_over_intake=intake_info["is_over_intake"],
        over_intake_count=intake_info["over_intake_count"],
        critical_flags_count=critical_count
    )
