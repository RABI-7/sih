from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.student import Student
from app.models.college import College


def check_batch_duplicates(batch_rows: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """
    Identifies APAAR IDs that appear multiple times within the same upload batch.
    Returns mapping of apaar_id -> list of 1-indexed row numbers.
    """
    apaar_map = {}
    for idx, row in enumerate(batch_rows, start=1):
        raw_id = row.get("apaar_id")
        if raw_id:
            cleaned = str(raw_id).strip()
            if cleaned:
                apaar_map.setdefault(cleaned, []).append(idx)
    
    # Filter only duplicates
    return {k: v for k, v in apaar_map.items() if len(v) > 1}


def check_intra_college_duplicate(db: Session, college_id: int, apaar_id: str, exclude_student_id: Optional[int] = None) -> Optional[Student]:
    """Checks if an APAAR ID already exists in the same college."""
    if not apaar_id:
        return None
    query = db.query(Student).filter(
        Student.college_id == college_id,
        Student.apaar_id == str(apaar_id).strip()
    )
    if exclude_student_id:
        query = query.filter(Student.id != exclude_student_id)
    return query.first()


def check_cross_college_duplicate(db: Session, current_college_id: int, apaar_id: str) -> List[Dict[str, Any]]:
    """
    Checks if an APAAR ID is enrolled in one or more OTHER colleges.
    Returns list of dicts with conflicting college details.
    """
    if not apaar_id:
        return []
    records = db.query(Student).join(College).filter(
        Student.college_id != current_college_id,
        Student.apaar_id == str(apaar_id).strip()
    ).all()

    conflicts = []
    for r in records:
        conflicts.append({
            "student_id": r.id,
            "student_name": r.student_name,
            "college_id": r.college_id,
            "college_name": r.college.name if r.college else "Unknown Institution",
            "programme": r.programme,
            "admission_date": r.admission_date
        })
    return conflicts
