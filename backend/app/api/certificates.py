import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.certificate import Certificate
from app.models.student import Student
from app.models.college import College
from app.schemas.certificate import (
    CertificateIssueRequest,
    CertificateResponse,
    CertificateVerifyResponse
)
from app.services.signing_service import (
    canonicalize_certificate_payload,
    sign_payload,
    verify_signature,
    generate_qr_data_uri
)
from app.services.audit_service import log_audit_event
from app.core.permissions import get_current_user

router = APIRouter(prefix="/certificates", tags=["Certificates & QR"])


@router.post("", response_model=CertificateResponse)
def issue_signed_certificate(
    payload: CertificateIssueRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    college = db.query(College).filter(College.id == student.college_id).first()
    college_name = college.name if college else "Registered Institution"

    # Canonical payload with minimal privacy-preserving fields
    cert_ref = f"CERT-APAAR-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=payload.expiry_months * 30)

    canonical_data = {
        "cert_id": cert_ref,
        "college_code": college.institution_code if college else "INST-001",
        "programme": student.programme,
        "student_ref": f"STU-{student.id}",
        "issued_at": now.isoformat(),
        "expires_at": expires_at.isoformat()
    }
    canonical_json_str = canonicalize_certificate_payload(canonical_data)
    digital_sig = sign_payload(canonical_json_str)

    verification_url = f"http://localhost:5173/verify?cert_ref={cert_ref}"
    qr_data_uri = generate_qr_data_uri(verification_url)

    certificate = Certificate(
        certificate_reference=cert_ref,
        student_id=student.id,
        college_id=student.college_id,
        canonical_payload=canonical_json_str,
        digital_signature=digital_sig,
        signature_algorithm="HMAC-SHA256",
        qr_code_data_uri=qr_data_uri,
        verification_url=verification_url,
        issued_at=now,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    log_audit_event(
        db=db,
        action="CERTIFICATE_ISSUED",
        entity_type="CERTIFICATE",
        entity_id=str(certificate.id),
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        college_id=student.college_id,
        metadata={
            "certificate_reference": cert_ref,
            "student_id": student.id,
            "digital_signature_prefix": digital_sig[:12] + "..."
        }
    )

    return CertificateResponse(
        id=certificate.id,
        certificate_reference=certificate.certificate_reference,
        student_id=student.id,
        student_name=student.student_name,
        college_name=college_name,
        programme=student.programme,
        academic_year=student.academic_year,
        canonical_payload=certificate.canonical_payload,
        digital_signature=certificate.digital_signature,
        signature_algorithm=certificate.signature_algorithm,
        qr_code_data_uri=certificate.qr_code_data_uri,
        verification_url=certificate.verification_url,
        issued_at=certificate.issued_at,
        expires_at=certificate.expires_at,
        is_revoked=certificate.is_revoked,
        revocation_reason=certificate.revocation_reason
    )


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate_by_id(certificate_id: int, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    student = cert.student
    college = cert.college
    return CertificateResponse(
        id=cert.id,
        certificate_reference=cert.certificate_reference,
        student_id=student.id if student else 0,
        student_name=student.student_name if student else "Student",
        college_name=college.name if college else "Registered Institution",
        programme=student.programme if student else "N/A",
        academic_year=student.academic_year if student else "2024-2025",
        canonical_payload=cert.canonical_payload,
        digital_signature=cert.digital_signature,
        signature_algorithm=cert.signature_algorithm,
        qr_code_data_uri=cert.qr_code_data_uri,
        verification_url=cert.verification_url,
        issued_at=cert.issued_at,
        expires_at=cert.expires_at,
        is_revoked=cert.is_revoked,
        revocation_reason=cert.revocation_reason
    )


@router.get("/verify/{certificate_reference}", response_model=CertificateVerifyResponse)
def verify_certificate_endpoint(certificate_reference: str, db: Session = Depends(get_db)):
    """
    Public QR verification endpoint.
    Checks digital signature, validity period, and revocation without exposing PII.
    """
    cert = db.query(Certificate).filter(
        Certificate.certificate_reference == certificate_reference.strip()
    ).first()

    if not cert:
        return CertificateVerifyResponse(
            is_valid=False,
            status="NOT_FOUND",
            message="No certificate matching this reference was found in the authoritative database.",
            digital_signature_verified=False
        )

    # 1. Cryptographically verify signature
    is_sig_valid = verify_signature(cert.canonical_payload, cert.digital_signature)
    if not is_sig_valid:
        return CertificateVerifyResponse(
            is_valid=False,
            status="INVALID_SIGNATURE",
            message="Cryptographic verification failed: Digital signature does not match canonical certificate data.",
            certificate_reference=cert.certificate_reference,
            digital_signature_verified=False
        )

    # 2. Check revocation
    if cert.is_revoked:
        return CertificateVerifyResponse(
            is_valid=False,
            status="REVOKED",
            message=f"Certificate has been revoked by the issuing institution. Reason: {cert.revocation_reason or 'Administrative revocation'}",
            certificate_reference=cert.certificate_reference,
            digital_signature_verified=True,
            issued_at=cert.issued_at,
            expires_at=cert.expires_at
        )

    # 3. Check expiration
    now = datetime.now(timezone.utc)
    exp = cert.expires_at.replace(tzinfo=timezone.utc) if cert.expires_at.tzinfo is None else cert.expires_at
    if now > exp:
        return CertificateVerifyResponse(
            is_valid=False,
            status="EXPIRED",
            message=f"Certificate expired on {exp.strftime('%Y-%m-%d')}.",
            certificate_reference=cert.certificate_reference,
            digital_signature_verified=True,
            issued_at=cert.issued_at,
            expires_at=cert.expires_at
        )

    student = cert.student
    college = cert.college
    college_name = college.name if college else "Registered Institution"

    return CertificateVerifyResponse(
        is_valid=True,
        status="VALID",
        message="Authentic certificate: Cryptographic signature verified and record is currently active.",
        certificate_reference=cert.certificate_reference,
        institution=college_name,
        programme=student.programme if student else "Certified Programme",
        student_reference=f"STU-****{student.id % 1000:03d}" if student else "STU-***",
        issued_at=cert.issued_at,
        expires_at=cert.expires_at,
        digital_signature_verified=True
    )
