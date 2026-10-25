from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    request_reference = Column(String(100), unique=True, nullable=False, index=True)
    verifier_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verifier_name = Column(String(255), nullable=False)
    purpose = Column(String(255), nullable=False)
    status = Column(String(50), default="pending_consent", nullable=False)  # pending_consent, consent_granted, consent_denied, expired, revoked
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="verification_requests")
    consents = relationship("Consent", back_populates="verification_request", cascade="all, delete-orphan")
