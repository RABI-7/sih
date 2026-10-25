import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

GENESIS_PREVIOUS_HASH = "0" * 64


def canonicalize_json(data: Optional[Dict[str, Any]]) -> str:
    if not data:
        return "{}"
    return json.dumps(data, sort_keys=True, separators=(',', ':'))


def compute_audit_hash(
    previous_hash: str,
    actor_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[str],
    timestamp_iso: str,
    metadata_json: str
) -> str:
    canonical_string = f"{previous_hash}|{actor_id or 0}|{action}|{entity_type}|{entity_id or ''}|{timestamp_iso}|{metadata_json}"
    return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()


def format_canonical_timestamp(dt: Any) -> str:
    if isinstance(dt, str):
        return dt[:19]
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    return str(dt)[:19]


def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    actor_id: Optional[int] = None,
    actor_name: str = "System",
    college_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """Appends a new immutable audit record to the hash chain."""
    last_entry = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last_entry.entry_hash if last_entry else GENESIS_PREVIOUS_HASH

    now = datetime.now(timezone.utc)
    timestamp_canonical = format_canonical_timestamp(now)
    meta_json_str = canonicalize_json(metadata)

    entry_hash = compute_audit_hash(
        previous_hash=previous_hash,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        timestamp_iso=timestamp_canonical,
        metadata_json=meta_json_str
    )

    log_entry = AuditLog(
        actor_id=actor_id,
        actor_name=actor_name,
        college_id=college_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        timestamp=now,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        metadata_json=meta_json_str
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def verify_audit_chain(db: Session) -> Tuple[bool, int, Optional[int], str]:
    """
    Verifies hash chain integrity from start to end.
    Returns (is_valid, total_verified, tampered_id, message).
    """
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not logs:
        return True, 0, None, "Audit log is empty; chain is valid."

    expected_prev = GENESIS_PREVIOUS_HASH
    for log in logs:
        # Check previous_hash link
        if log.previous_hash != expected_prev:
            return False, len(logs), log.id, f"Chain broken at entry ID {log.id}: previous_hash does not match preceding entry_hash."

        # Recompute entry_hash
        timestamp_canonical = format_canonical_timestamp(log.timestamp)
        meta_str = log.metadata_json or "{}"
        
        recomputed = compute_audit_hash(
            previous_hash=log.previous_hash,
            actor_id=log.actor_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            timestamp_iso=timestamp_canonical,
            metadata_json=meta_str
        )

        if recomputed != log.entry_hash:
            return False, len(logs), log.id, f"Tampered entry detected at ID {log.id}: entry_hash does not match recomputed SHA-256."

        expected_prev = log.entry_hash

    return True, len(logs), None, f"Audit chain intact and verified across all {len(logs)} entries."
