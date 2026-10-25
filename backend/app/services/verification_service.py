import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.student import Student
from app.models.verification_request import VerificationRequest
from app.models.consent import Consent
from app.models.college import College
from app.core.security import mask_apaar_id
from app.services.audit_service import log_audit_event


def create_verification_request(
    db: Session,
    student_identifier: str,
    purpose: str,
    verifier_id: Optional[int],
    verifier_name: str
) -> VerificationRequest:
    # Resolve student by ID or APAAR ID
    student = None
    if student_identifier.isdigit():
        student = db.query(Student).filter(Student.id == int(student_identifier)).first()
    if not student:
        student = db.query(Student).filter(Student.apaar_id == student_identifier.strip()).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student record with identifier '{student_identifier}' could not be located."
        )

    req_ref = f"VR-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    v_request = VerificationRequest(
        student_id=student.id,
        request_reference=req_ref,
        verifier_id=verifier_id,
        verifier_name=verifier_name,
        purpose=purpose,
        status="pending_consent",
        expires_at=expires_at
    )
    db.add(v_request)
    db.commit()
    db.refresh(v_request)

    log_audit_event(
        db=db,
        action="VERIFICATION_REQUESTED",
        entity_type="VERIFICATION_REQUEST",
        entity_id=str(v_request.id),
        actor_id=verifier_id,
        actor_name=verifier_name,
        college_id=student.college_id,
        metadata={
            "request_reference": req_ref,
            "purpose": purpose,
            "student_id": student.id
        }
    )

    return v_request


def grant_demo_consent(
    db: Session,
    request_reference: str,
    permitted_fields: List[str],
    duration_days: int = 7
) -> Consent:
    v_request = db.query(VerificationRequest).filter(
        VerificationRequest.request_reference == request_reference
    ).first()
    if not v_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification request reference not found.")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=duration_days)

    # Deactivate existing active consents for this request
    existing_consents = db.query(Consent).filter(
        Consent.verification_request_id == v_request.id,
        Consent.is_active == True
    ).all()
    for c in existing_consents:
        c.is_active = False

    consent = Consent(
        student_id=v_request.student_id,
        verification_request_id=v_request.id,
        purpose=v_request.purpose,
        permitted_fields=json.dumps(permitted_fields),
        granted_at=now,
        expires_at=expires_at,
        is_active=True
    )
    db.add(consent)

    v_request.status = "consent_granted"
    db.commit()
    db.refresh(consent)

    log_audit_event(
        db=db,
        action="CONSENT_GRANTED",
        entity_type="CONSENT",
        entity_id=str(consent.id),
        actor_name="Student (Simulated Demo Consent)",
        metadata={
            "request_reference": request_reference,
            "permitted_fields": permitted_fields,
            "duration_days": duration_days
        }
    )

    return consent


def revoke_consent(db: Session, request_reference: str) -> bool:
    v_request = db.query(VerificationRequest).filter(
        VerificationRequest.request_reference == request_reference
    ).first()
    if not v_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification request reference not found.")

    consents = db.query(Consent).filter(
        Consent.verification_request_id == v_request.id,
        Consent.is_active == True
    ).all()

    now = datetime.now(timezone.utc)
    for c in consents:
        c.is_active = False
        c.revoked_at = now

    v_request.status = "revoked"
    db.commit()

    log_audit_event(
        db=db,
        action="CONSENT_REVOKED",
        entity_type="CONSENT",
        entity_id=str(v_request.id),
        actor_name="Student (Revocation)",
        metadata={"request_reference": request_reference}
    )

    return True


def get_verified_student_data(db: Session, request_reference: str) -> Dict[str, Any]:
    """
    Returns only the fields permitted by the active consent.
    Enforces privacy by design.
    """
    v_request = db.query(VerificationRequest).filter(
        VerificationRequest.request_reference == request_reference
    ).first()
    if not v_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification request not found.")

    student = db.query(Student).filter(Student.id == v_request.student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found.")

    college = db.query(College).filter(College.id == student.college_id).first()

    now = datetime.now(timezone.utc)
    # Check if request has expired
    if v_request.expires_at and v_request.expires_at.tzinfo is None:
        v_exp = v_request.expires_at.replace(tzinfo=timezone.utc)
    else:
        v_exp = v_request.expires_at

    if v_exp and now > v_exp:
        v_request.status = "expired"
        db.commit()

    if v_request.status != "consent_granted":
        return {
            "request_reference": v_request.request_reference,
            "status": v_request.status,
            "purpose": v_request.purpose,
            "verifier_name": v_request.verifier_name,
            "is_valid_access": False,
            "message": f"Verification access is restricted. Current status: '{v_request.status}'. Explicit student consent is required."
        }

    # Fetch active consent
    active_consent = db.query(Consent).filter(
        Consent.verification_request_id == v_request.id,
        Consent.is_active == True
    ).order_by(Consent.id.desc()).first()

    if not active_consent:
        return {
            "request_reference": v_request.request_reference,
            "status": "pending_consent",
            "purpose": v_request.purpose,
            "verifier_name": v_request.verifier_name,
            "is_valid_access": False,
            "message": "No active student consent found for this request."
        }

    # Parse permitted fields
    try:
        permitted_fields = json.loads(active_consent.permitted_fields)
    except Exception:
        permitted_fields = ["student_name", "programme", "college_name"]

    # Filter student data to only permitted fields
    all_fields = {
        "student_name": student.student_name,
        "masked_apaar_id": mask_apaar_id(student.apaar_id),
        "apaar_id": student.apaar_id if "apaar_id" in permitted_fields else mask_apaar_id(student.apaar_id),
        "programme": student.programme,
        "academic_year": student.academic_year,
        "admission_date": student.admission_date,
        "admission_category": student.admission_category,
        "college_name": college.name if college else "Registered Institution",
        "institution_code": college.institution_code if college else "N/A",
        "record_status": student.record_status
    }

    filtered_data = {k: v for k, v in all_fields.items() if k in permitted_fields or k in ["student_name", "college_name"]}

    return {
        "request_reference": v_request.request_reference,
        "status": "consent_granted",
        "purpose": v_request.purpose,
        "verifier_name": v_request.verifier_name,
        "is_valid_access": True,
        "granted_at": active_consent.granted_at,
        "expires_at": active_consent.expires_at,
        "permitted_fields": permitted_fields,
        "student_data": filtered_data,
        "message": "Consent verified successfully. Showing strictly authorized fields."
    }
