from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.verification import (
    VerificationRequestCreate,
    VerificationRequestResponse,
    ConsentGrantRequest,
    VerificationResultResponse
)
from app.services.verification_service import (
    create_verification_request,
    grant_demo_consent,
    revoke_consent,
    get_verified_student_data
)
from app.models.verification_request import VerificationRequest
from app.core.security import mask_apaar_id
from app.core.permissions import get_current_user

router = APIRouter(prefix="/verification-requests", tags=["Verification"])


@router.post("", response_model=VerificationRequestResponse)
def new_verification_request(
    payload: VerificationRequestCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    v_req = create_verification_request(
        db=db,
        student_identifier=payload.student_identifier,
        purpose=payload.purpose,
        verifier_id=current_user.id,
        verifier_name=current_user.full_name
    )

    return VerificationRequestResponse(
        id=v_req.id,
        request_reference=v_req.request_reference,
        student_id=v_req.student_id,
        student_name=v_req.student.student_name if v_req.student else "Student",
        masked_apaar_id=mask_apaar_id(v_req.student.apaar_id if v_req.student else ""),
        purpose=v_req.purpose,
        verifier_name=v_req.verifier_name,
        status=v_req.status,
        created_at=v_req.created_at,
        expires_at=v_req.expires_at
    )


@router.post("/{request_reference}/demo-consent")
def simulate_student_consent(
    request_reference: str,
    payload: ConsentGrantRequest,
    db: Session = Depends(get_db)
):
    """
    Simulated demo consent step: Student selects permitted fields and grants time-limited authorization.
    """
    consent = grant_demo_consent(
        db=db,
        request_reference=request_reference,
        permitted_fields=payload.permitted_fields,
        duration_days=payload.duration_days
    )
    return {
        "status": "success",
        "message": "Demo consent granted successfully. Permitted fields recorded.",
        "request_reference": request_reference,
        "expires_at": consent.expires_at
    }


@router.get("/{request_reference}/result", response_model=VerificationResultResponse)
def get_verification_result(request_reference: str, db: Session = Depends(get_db)):
    result = get_verified_student_data(db, request_reference)
    return VerificationResultResponse(**result)


@router.post("/{request_reference}/revoke")
def revoke_verification_consent(request_reference: str, db: Session = Depends(get_db)):
    revoke_consent(db, request_reference)
    return {
        "status": "revoked",
        "message": "Consent successfully revoked. Verifier access terminated.",
        "request_reference": request_reference
    }
