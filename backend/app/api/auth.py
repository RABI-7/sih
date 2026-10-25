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

router = APIRouter(prefix="/auth", tags=["Authentication"])

DEMO_ACCOUNTS = {
    "college_admin_1": {
        "email": "admin@delhi-tech.edu.in",
        "name": "Prof. R. Sharma (College Admin)",
        "role": "college_admin",
        "institution_code": "INST-001"
    },
    "college_admin_2": {
        "email": "admin@national-engg.edu.in",
        "name": "Dr. Sunita Verma (College Admin)",
        "role": "college_admin",
        "institution_code": "INST-002"
    },
    "compliance_officer": {
        "email": "compliance@aicte-council.gov.in",
        "name": "Vikram Malhotra (AICTE Compliance Officer)",
        "role": "compliance_officer",
        "institution_code": None
    },
    "verifier": {
        "email": "verifier@credential-check.org",
        "name": "Ananya Sen (Academic Credential Verifier)",
        "role": "verifier",
        "institution_code": None
    }
}


@router.post("/demo-login")
def demo_login(payload: DemoLoginRequest):
    """
    Demo login step 1: Select demo account.
    Returns prompt to enter the demo OTP (123456).
    """
    account = DEMO_ACCOUNTS.get(payload.account_key)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo account key. Available keys: {list(DEMO_ACCOUNTS.keys())}"
        )
    return {
        "message": f"OTP sent to {account['email']} (DEMO OTP: {settings.DEMO_OTP})",
        "account_key": payload.account_key,
        "email": account["email"],
        "demo_otp_hint": settings.DEMO_OTP
    }


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Demo login step 2: Verify OTP and issue JWT access token.
    """
    account_info = DEMO_ACCOUNTS.get(payload.account_key)
    if not account_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown account key")

    if payload.otp != settings.DEMO_OTP:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP. Use demo OTP: 123456")

    # Fetch or provision demo user
    user = db.query(User).filter(User.email == account_info["email"]).first()
    if not user:
        college_id = None
        if account_info["institution_code"]:
            college = db.query(College).filter(College.institution_code == account_info["institution_code"]).first()
            if college:
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
        metadata={"role": user.role, "auth_method": "demo_otp"}
    )

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
