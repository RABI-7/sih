from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_reference = Column(String(100), unique=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    canonical_payload = Column(Text, nullable=False)
    digital_signature = Column(Text, nullable=False)
    signature_algorithm = Column(String(50), default="HMAC-SHA256", nullable=False)
    qr_code_data_uri = Column(Text, nullable=False)
    verification_url = Column(String(500), nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    revocation_reason = Column(String(255), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="certificates")
    college = relationship("College")
