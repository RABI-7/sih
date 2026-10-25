import hmac
import hashlib
import json
import base64
import io
import qrcode
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from app.core.config import settings


def canonicalize_certificate_payload(payload: Dict[str, Any]) -> str:
    """Produces deterministic canonical JSON formatting for cryptographic signing."""
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


def sign_payload(canonical_json: str) -> str:
    """Generates cryptographic HMAC-SHA256 digital signature."""
    secret_key = settings.SIGNING_SECRET.encode("utf-8")
    sig = hmac.new(secret_key, canonical_json.encode("utf-8"), hashlib.sha256).hexdigest()
    return sig


def verify_signature(canonical_json: str, signature: str) -> bool:
    """Cryptographically verifies that the payload was signed with the server's private signing key."""
    expected_sig = sign_payload(canonical_json)
    return hmac.compare_digest(expected_sig, signature)


def generate_qr_data_uri(content_url: str) -> str:
    """Generates a high-contrast QR code image as a Base64 data URI."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(content_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0F2744", back_color="#FFFFFF")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"
