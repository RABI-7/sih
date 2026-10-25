from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.college import College
from app.models.student import Student


def get_college_intake_status(db: Session, college_id: int, prospective_count: int = 0) -> Dict[str, Any]:
    college = db.query(College).filter(College.id == college_id).first()
    if not college:
        return {
            "approved_intake": 0,
            "current_enrolled": 0,
            "projected_total": 0,
            "utilization_rate": 0.0,
            "is_over_intake": False,
            "over_intake_count": 0
        }

    current_enrolled = db.query(Student).filter(
        Student.college_id == college_id,
        Student.record_status != "invalid"
    ).count()

    projected_total = current_enrolled + prospective_count
    approved = college.approved_intake or 1

    utilization_rate = round((projected_total / approved) * 100.0, 1)
    is_over_intake = projected_total > approved
    over_intake_count = max(0, projected_total - approved)

    return {
        "college_id": college.id,
        "college_name": college.name,
        "approved_intake": approved,
        "current_enrolled": current_enrolled,
        "projected_total": projected_total,
        "utilization_rate": utilization_rate,
        "is_over_intake": is_over_intake,
        "over_intake_count": over_intake_count
    }
