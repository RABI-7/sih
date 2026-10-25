import pytest
from app.services.signing_service import (
    canonicalize_certificate_payload,
    sign_payload,
    verify_signature,
    generate_qr_data_uri
)


def test_cryptographic_signature_validity():
    payload = {
        "cert_id": "CERT-2026-001",
        "student_ref": "STU-1234",
        "college_code": "INST-001",
        "issued_at": "2026-01-01T00:00:00Z"
    }
    canonical = canonicalize_certificate_payload(payload)
    sig = sign_payload(canonical)

    assert len(sig) == 64  # SHA-256 hex
    assert verify_signature(canonical, sig) is True


def test_tampered_payload_signature_fails():
    payload = {"cert_id": "CERT-2026-001", "grade": "PASS"}
    canonical = canonicalize_certificate_payload(payload)
    sig = sign_payload(canonical)

    tampered_canonical = canonical.replace("PASS", "DISTINCTION")
    assert verify_signature(tampered_canonical, sig) is False


def test_qr_generation():
    url = "http://localhost:5173/verify?cert_ref=CERT-TEST-123"
    qr_data_uri = generate_qr_data_uri(url)
    assert qr_data_uri.startswith("data:image/png;base64,")
