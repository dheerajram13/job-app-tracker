from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)  # e.g., "Software Engineer Resume", "Data Scientist Resume"
    file_path = Column(String)  # Path to stored resume file
    file_type = Column(String)  # e.g., "pdf", "doc", "docx"
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Flag for current/archived resumes
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="resumes")
    
    # Additional metadata fields
    version = Column(Integer, default=1)  # Track resume versions
    description = Column(String, nullable=True)  # Optional description/notes
    tags = Column(String, nullable=True)  # Comma-separated tags for categorization