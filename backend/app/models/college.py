from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    institution_code = Column(String(50), nullable=False, unique=True, index=True)
    approved_intake = Column(Integer, nullable=False, default=120)
    category = Column(String(100), default="Engineering & Technology")
    state = Column(String(100), default="Delhi NCT")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", back_populates="college", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="college", cascade="all, delete-orphan")
    batches = relationship("UploadBatch", back_populates="college", cascade="all, delete-orphan")
