from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class JobStatus(str, enum.Enum):
    APPLIED = "Applied"
    PHONE_SCREEN = "Phone Screen"
    TECHNICAL = "Technical Interview"
    ONSITE = "On-site"
    OFFER = "Offer"
    REJECTED = "Rejected"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    status = Column(String(50), default="Applied")  # Changed from Enum to String for flexibility
    date_applied = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    salary_range = Column(String(100), nullable=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    relevance_score = Column(Float, default=0.0)
    skills = Column(Text, nullable=True)
    is_scraped = Column(Boolean, default=False)
    search_query = Column(String(255), nullable=True)
        
    # Define the relationships
    user = relationship("User", back_populates="jobs")
    resume = relationship("Resume", back_populates="jobs")