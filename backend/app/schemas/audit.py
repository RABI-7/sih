from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: int
    actor_id: Optional[int] = None
    actor_name: str
    college_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    timestamp: datetime
    previous_hash: str
    entry_hash: str
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class AuditIntegrityResponse(BaseModel):
    is_valid: bool
    total_entries_verified: int
    genesis_hash_valid: bool
    tampered_entry_id: Optional[int] = None
    verification_message: str
    verified_at: datetime
