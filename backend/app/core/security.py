import re
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from app.core.config import settings


def get_password_hash(password: str) -> str:
    """Generates salted SHA-256 hash for authentication."""
    salted = f"{settings.SECRET_KEY}:{password}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored salted hash."""
    expected = get_password_hash(plain_password)
    return hashlib.sha256(expected.encode()).hexdigest() == hashlib.sha256(hashed_password.encode()).hexdigest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None


def mask_apaar_id(apaar_id: Optional[str]) -> str:
    """Masks a 12-digit APAAR ID to protect student privacy: e.g. 901234567890 -> XXXX-XXXX-7890"""
    if not apaar_id:
        return "N/A"
    clean_id = re.sub(r"\D", "", str(apaar_id))
    if len(clean_id) >= 4:
        last4 = clean_id[-4:]
        return f"XXXX-XXXX-{last4}"
    return "XXXX-XXXX-XXXX"


def is_valid_apaar_format(apaar_id: Optional[str]) -> bool:
    """Checks whether the APAAR ID is strictly 12 digits numeric without non-digit characters."""
    if not apaar_id:
        return False
    val = str(apaar_id).strip()
    return bool(re.match(r"^\d{12}$", val))
