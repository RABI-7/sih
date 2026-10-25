from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class ValidationFlag(Base):
    __tablename__ = "validation_flags"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index = Column(Integer, nullable=True)
    rule_code = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False)  # critical, high, moderate, low
    explanation = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=True)
    status = Column(String(50), default="open", nullable=False)  # open, under_review, resolved, false_positive
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="flags")
    batch = relationship("UploadBatch", back_populates="flags")
