from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    apaar_id = Column(String(50), nullable=True, index=True)  # Allowed null/duplicate for audit & validation tracking
    student_name = Column(String(255), nullable=False)
    programme = Column(String(150), nullable=False)
    academic_year = Column(String(50), nullable=False)
    admission_date = Column(String(50), nullable=True)
    admission_category = Column(String(50), default="General")
    source_batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    record_status = Column(String(50), default="valid", nullable=False)  # valid, warning, invalid
    risk_score = Column(Float, default=0.0, nullable=False)
    anomaly_score = Column(Float, default=0.0, nullable=True)  # Experimental Isolation Forest score
    raw_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    college = relationship("College", back_populates="students")
    batch = relationship("UploadBatch", back_populates="students")
    flags = relationship("ValidationFlag", back_populates="student", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="student", cascade="all, delete-orphan")
    verification_requests = relationship("VerificationRequest", back_populates="student", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="student", cascade="all, delete-orphan")
