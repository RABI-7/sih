from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_sha256 = Column(String(64), nullable=False, index=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    processing_status = Column(String(50), default="completed", nullable=False)  # pending, completed, failed
    total_rows = Column(Integer, default=0, nullable=False)
    accepted_rows = Column(Integer, default=0, nullable=False)
    rejected_rows = Column(Integer, default=0, nullable=False)
    warning_rows = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    college = relationship("College", back_populates="batches")
    students = relationship("Student", back_populates="batch", cascade="all, delete-orphan")
    flags = relationship("ValidationFlag", back_populates="batch", cascade="all, delete-orphan")
