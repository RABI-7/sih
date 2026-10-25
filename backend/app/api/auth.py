import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.college import College
from app.schemas.auth import DemoLoginRequest, VerifyOtpRequest, TokenResponse, UserResponse
from app.services.audit_service import log_audit_event

logger = logging.getLogger("apaar_guardian.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

DEMO_ACCOUNTS = {
    "college_admin_1": {
        "email": "admin@delhi-tech.edu.in",
        "name": "Prof. R. Sharma (College Admin)",
        "role": "college_admin",
        "institution_code": "INST-001",
        "college_name": "Delhi Institute of Technology & Applied Sciences"
    },
    "college_admin_2": {
        "email": "admin@national-engg.edu.in",
        "name": "Dr. Sunita Verma (College Admin)",
        "role": "college_admin",
        "institution_code": "INST-002",
        "college_name": "National College of Engineering & Research"
    },
    "compliance_officer": {
        "email": "compliance@aicte-council.gov.in",
        "name": "Vikram Malhotra (AICTE Compliance Officer)",
        "role": "compliance_officer",
        "institution_code": None,
        "college_name": None
    },
    "verifier": {
        "email": "verifier@credential-check.org",
        "name": "Ananya Sen (Academic Credential Verifier)",
        "role": "verifier",
        "institution_code": None,
        "college_name": None
    }
}


def get_canonical_demo_otp() -> str:
    """Returns the standardized prototype OTP string, stripped of extra quotes or whitespace."""
    raw = settings.DEMO_OTP if settings.DEMO_OTP else "123456"
    clean = str(raw).strip().strip('"\'')
    return clean if clean else "123456"


@router.post("/demo-login")
def demo_login(payload: DemoLoginRequest):
    """
    Demo login step 1: Select demo account.
    Validates account key and returns deterministic demo OTP hint.
    """
    account_key = (payload.account_key or "").strip()
    logger.info("Demo login requested for account_key: '%s'", account_key)

    account = DEMO_ACCOUNTS.get(account_key)
    if not account:
        logger.warning("Demo login failed: unsupported account_key '%s'", account_key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo account key '{account_key}'. Supported accounts: {', '.join(DEMO_ACCOUNTS.keys())}"
        )

    canonical_otp = get_canonical_demo_otp()
    return {
        "message": f"Demo OTP issued for {account['email']} (DEMO OTP: {canonical_otp})",
        "account_key": account_key,
        "email": account["email"],
        "demo_otp_hint": canonical_otp,
        "role": account["role"]
    }


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Demo login step 2: Verify OTP and issue JWT access token.
    Deterministic: '123456' is guaranteed to authenticate for supported demo accounts.
    """
    account_key = (payload.account_key or "").strip()
    submitted_otp = str(payload.otp or "").strip()

    logger.info("Verifying OTP for account_key: '%s' (otp_length: %d)", account_key, len(submitted_otp))

    account_info = DEMO_ACCOUNTS.get(account_key)
    if not account_info:
        logger.warning("OTP verification rejected: unknown account_key '%s'", account_key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown account key '{account_key}'. Supported accounts: {', '.join(DEMO_ACCOUNTS.keys())}"
        )

    # Valid OTP set: accepts both configured DEMO_OTP and canonical '123456'
    canonical_otp = get_canonical_demo_otp()
    allowed_otps = {canonical_otp, "123456"}

    if submitted_otp not in allowed_otps:
        logger.warning("OTP verification rejected for account_key '%s': invalid OTP submitted", account_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid OTP. Use demo OTP: {canonical_otp}"
        )

    # Fetch or provision demo user
    user = db.query(User).filter(User.email == account_info["email"]).first()
    if not user:
        college_id = None
        if account_info["institution_code"]:
            college = db.query(College).filter(College.institution_code == account_info["institution_code"]).first()
            if not college:
                # Auto-provision institution college if running on fresh database (e.g. initial Render launch)
                college = College(
                    name=account_info["college_name"] or f"Institution {account_info['institution_code']}",
                    institution_code=account_info["institution_code"],
                    approved_intake=120,
                    category="Engineering & Technology",
                    state="Delhi NCT",
                    is_active=True
                )
                db.add(college)
                db.commit()
                db.refresh(college)
            college_id = college.id

        user = User(
            email=account_info["email"],
            full_name=account_info["name"],
            role=account_info["role"],
            college_id=college_id,
            hashed_password="demo_hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Auto-provisioned demo user ID %d for account '%s' (role: %s)", user.id, account_key, user.role)
    else:
        # If user exists but college_id was unlinked and institution_code is needed, resolve it
        if not user.college_id and account_info["institution_code"]:
            college = db.query(College).filter(College.institution_code == account_info["institution_code"]).first()
            if college:
                user.college_id = college.id
                db.commit()
                db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role, "college_id": user.college_id})

    college_name = user.college.name if user.college else None
    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        college_id=user.college_id,
        college_name=college_name
    )

    log_audit_event(
        db=db,
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=str(user.id),
        actor_id=user.id,
        actor_name=user.full_name,
        college_id=user.college_id,
        metadata={"role": user.role, "auth_method": "demo_otp", "account_key": account_key}
    )

    logger.info("Authentication successful for user ID %d (account_key: '%s', role: '%s')", user.id, account_key, user.role)

    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    college_name = current_user.college.name if current_user.college else None
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        college_id=current_user.college_id,
        college_name=college_name
    )
