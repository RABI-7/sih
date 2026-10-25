from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_request_id = Column(Integer, ForeignKey("verification_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose = Column(String(255), nullable=False)
    permitted_fields = Column(Text, nullable=False)  # JSON-encoded array of allowed field names
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="consents")
    verification_request = relationship("VerificationRequest", back_populates="consents")
