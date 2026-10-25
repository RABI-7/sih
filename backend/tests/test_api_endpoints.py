import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.student import Student
from app.models.college import College

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_demo_login_flow():
    # Step 1: Demo login valid account
    res1 = client.post("/api/auth/demo-login", json={"account_key": "college_admin_1"})
    assert res1.status_code == 200
    assert "Demo OTP issued" in res1.json()["message"]
    assert res1.json()["demo_otp_hint"] == "123456"

    # Step 2: Verify OTP
    res2 = client.post("/api/auth/verify-otp", json={"account_key": "college_admin_1", "otp": "123456"})
    assert res2.status_code == 200
    token_data = res2.json()
    assert "access_token" in token_data
    assert token_data["user"]["role"] == "college_admin"
    assert token_data["user"]["college_id"] == 1


def test_demo_login_unsupported_account_key():
    # Attempting to login with unsupported key should return 400
    res = client.post("/api/auth/demo-login", json={"account_key": "unsupported_unknown_role"})
    assert res.status_code == 400
    assert "Invalid demo account key" in res.json()["detail"]


def test_verify_otp_invalid_code():
    # Attempting wrong OTP returns 401
    res = client.post("/api/auth/verify-otp", json={"account_key": "college_admin_1", "otp": "999999"})
    assert res.status_code == 401
    assert "Invalid OTP" in res.json()["detail"]


def test_verify_otp_whitespace_normalization():
    # Extra whitespace around OTP or account_key should be stripped safely
    res = client.post("/api/auth/verify-otp", json={"account_key": "  college_admin_1  ", "otp": " 123456 "})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_all_supported_demo_roles_login_deterministically():
    roles = [
        ("college_admin_1", "college_admin"),
        ("college_admin_2", "college_admin"),
        ("compliance_officer", "compliance_officer"),
        ("verifier", "verifier"),
    ]
    for key, expected_role in roles:
        # Step 1: Request demo login
        res1 = client.post("/api/auth/demo-login", json={"account_key": key})
        assert res1.status_code == 200, f"demo-login failed for {key}"
        # Step 2: Verify with canonical 123456
        res2 = client.post("/api/auth/verify-otp", json={"account_key": key, "otp": "123456"})
        assert res2.status_code == 200, f"verify-otp failed for {key}"
        assert res2.json()["user"]["role"] == expected_role


def test_tenant_isolation_enforcement():
    # Login as College 1 Admin
    res = client.post("/api/auth/verify-otp", json={"account_key": "college_admin_1", "otp": "123456"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Allowed: Request students of College 1
    res_ok = client.get("/api/students?college_id=1", headers=headers)
    assert res_ok.status_code == 200

    # Forbidden: Request students of College 2 -> Should return 403 Forbidden!
    res_forbidden = client.get("/api/students?college_id=2", headers=headers)
    assert res_forbidden.status_code == 403
    assert "Tenant isolation violation" in res_forbidden.json()["detail"]


def test_compliance_summary_endpoint():
    res = client.post("/api/auth/verify-otp", json={"account_key": "compliance_officer", "otp": "123456"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/compliance/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_institutions"] == 3
    assert data["total_students"] > 0
    assert len(data["risk_distribution"]) == 4


def test_consent_based_verification_lifecycle():
    # 1. Login as Verifier
    v_res = client.post("/api/auth/verify-otp", json={"account_key": "verifier", "otp": "123456"})
    v_token = v_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {v_token}"}

    # Find a test student
    db = SessionLocal()
    student = db.query(Student).filter(Student.record_status == "valid").first()
    student_id = student.id
    db.close()

    # 2. Create Verification Request
    req_res = client.post(
        "/api/verification-requests",
        json={
            "student_identifier": str(student_id),
            "purpose": "Employment Background Verification",
            "verifier_name": "TCS Global Verification Team"
        },
        headers=headers
    )
    assert req_res.status_code == 200
    v_data = req_res.json()
    ref = v_data["request_reference"]
    assert v_data["status"] == "pending_consent"

    # 3. Access before consent -> should be restricted
    res_pre = client.get(f"/api/verification-requests/{ref}/result")
    assert res_pre.status_code == 200
    assert res_pre.json()["is_valid_access"] is False

    # 4. Student grants simulated demo consent with permitted fields
    consent_res = client.post(
        f"/api/verification-requests/{ref}/demo-consent",
        json={
            "permitted_fields": ["student_name", "programme", "college_name"],
            "duration_days": 5
        }
    )
    assert consent_res.status_code == 200

    # 5. Access after consent -> authorized and strictly field-limited
    res_post = client.get(f"/api/verification-requests/{ref}/result")
    assert res_post.status_code == 200
    post_data = res_post.json()
    assert post_data["is_valid_access"] is True
    assert "student_name" in post_data["student_data"]
    assert "programme" in post_data["student_data"]
    # Raw personal fields not in permitted_fields should NOT be present
    assert "admission_category" not in post_data["student_data"]

    # 6. Revoke Consent
    rev_res = client.post(f"/api/verification-requests/{ref}/revoke")
    assert rev_res.status_code == 200

    # 7. Access after revocation -> denied
    res_revoked = client.get(f"/api/verification-requests/{ref}/result")
    assert res_revoked.status_code == 200
    assert res_revoked.json()["is_valid_access"] is False


def test_certificate_issuance_and_qr_verification():
    db = SessionLocal()
    student = db.query(Student).filter(Student.record_status == "valid").first()
    student_id = student.id
    db.close()

    res = client.post("/api/auth/verify-otp", json={"account_key": "college_admin_1", "otp": "123456"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Issue certificate
    cert_res = client.post(
        "/api/certificates",
        json={"student_id": student_id, "expiry_months": 12},
        headers=headers
    )
    assert cert_res.status_code == 200
    cert = cert_res.json()
    assert cert["digital_signature"] is not None
    assert cert["qr_code_data_uri"].startswith("data:image/png;base64,")

    # Verify certificate via public endpoint
    verify_res = client.get(f"/api/certificates/verify/{cert['certificate_reference']}")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["status"] == "VALID"
    assert verify_data["digital_signature_verified"] is True
