import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.models.audit_log import AuditLog
from app.services.audit_service import log_audit_event, verify_audit_chain, GENESIS_PREVIOUS_HASH


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_audit_hash_chain_valid(test_db):
    # Log 3 events
    e1 = log_audit_event(test_db, action="EVENT_1", entity_type="TEST", actor_name="Actor 1")
    assert e1.previous_hash == GENESIS_PREVIOUS_HASH

    e2 = log_audit_event(test_db, action="EVENT_2", entity_type="TEST", actor_name="Actor 2")
    assert e2.previous_hash == e1.entry_hash

    e3 = log_audit_event(test_db, action="EVENT_3", entity_type="TEST", actor_name="Actor 3")
    assert e3.previous_hash == e2.entry_hash

    # Verify chain
    is_valid, count, tampered_id, msg = verify_audit_chain(test_db)
    assert is_valid is True
    assert count == 3
    assert tampered_id is None


def test_audit_hash_chain_tamper_detection(test_db):
    log_audit_event(test_db, action="EVENT_1", entity_type="TEST")
    e2 = log_audit_event(test_db, action="EVENT_2", entity_type="TEST")
    log_audit_event(test_db, action="EVENT_3", entity_type="TEST")

    # Manually tamper with entry 2 in database
    e2.action = "TAMPERED_ACTION_MALICIOUS"
    test_db.commit()

    # Re-verify chain - tampering must be detected!
    is_valid, count, tampered_id, msg = verify_audit_chain(test_db)
    assert is_valid is False
    assert tampered_id == e2.id
    assert "Tampered entry detected" in msg or "Chain broken" in msg
