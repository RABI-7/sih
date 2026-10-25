import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse, AuditIntegrityResponse
from app.services.audit_service import verify_audit_chain, log_audit_event
from app.core.permissions import get_current_user

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None),
    college_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if college_id:
        query = query.filter(AuditLog.college_id == college_id)

    logs = query.order_by(AuditLog.id.desc()).offset(offset).limit(limit).all()
    results = []
    for l in logs:
        meta_dict = None
        if l.metadata_json:
            try:
                meta_dict = json.loads(l.metadata_json)
            except Exception:
                meta_dict = {"raw": l.metadata_json}

        results.append(AuditLogResponse(
            id=l.id,
            actor_id=l.actor_id,
            actor_name=l.actor_name,
            college_id=l.college_id,
            action=l.action,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            timestamp=l.timestamp,
            previous_hash=l.previous_hash,
            entry_hash=l.entry_hash,
            metadata=meta_dict
        ))
    return results


@router.post("/verify-integrity", response_model=AuditIntegrityResponse)
def run_audit_integrity_check(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Verifies every cryptographic link in the tamper-evident SHA-256 audit chain.
    """
    is_valid, total_checked, tampered_id, message = verify_audit_chain(db)
    
    # Also log that an integrity verification was performed
    log_audit_event(
        db=db,
        action="INTEGRITY_CHECK_EXECUTED",
        entity_type="AUDIT_CHAIN",
        entity_id=str(total_checked),
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        metadata={"is_valid": is_valid, "total_verified": total_checked, "tampered_id": tampered_id}
    )

    return AuditIntegrityResponse(
        is_valid=is_valid,
        total_entries_verified=total_checked,
        genesis_hash_valid=True,
        tampered_entry_id=tampered_id,
        verification_message=message,
        verified_at=datetime.now(timezone.utc)
    )
